"""Who a teammate is, and where they work: given away, and traced."""

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.users.application.dtos.user_dto import UpdateUserIdentityCommand
from src.modules.users.application.use_cases.update_user_identity import (
    UpdateUserIdentityUseCase,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.enums.department import Department
from src.shared.enums.org_level import OrgLevel
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryUserRepository,
)


def make_manager() -> User:
    return User(
        id=1,
        entra_oid="oid-manager",
        email="j.buget@waat.fr",
        display_name="J. Buget",
        role=Role.MANAGER,
    )


def make_teammate() -> User:
    return User(
        id=2,
        entra_oid="oid-teammate",
        email="l.chen@waat.fr",
        display_name="L. Chen",
        role=Role.TEAMMATE,
    )


def build(users: list[User]):
    repo = InMemoryUserRepository(users)
    audit = InMemoryAuditLogRepository()
    return UpdateUserIdentityUseCase(users=repo, audit_logs=audit), repo, audit


def command(**overrides) -> UpdateUserIdentityCommand:
    fields: dict = {
        "actor_id": 1,
        "target_user_id": 2,
        "first_name": "Léa",
        "last_name": "Chen",
        "department": Department.CUSTOMER_SERVICE,
        "github_username": "lea-chen",
        "org_level": OrgLevel.COMOP,
    }
    fields.update(overrides)
    return UpdateUserIdentityCommand(**fields)


async def test_a_manager_gives_away_who_a_teammate_is() -> None:
    use_case, repo, _ = build([make_manager(), make_teammate()])

    await use_case.execute(command())

    teammate = await repo.get_by_id(2)
    assert teammate is not None
    assert teammate.first_name == "Léa"
    assert teammate.last_name == "Chen"
    assert teammate.department is Department.CUSTOMER_SERVICE


async def test_what_is_left_blank_is_emptied() -> None:
    """The sheet is written whole: an emptied field is a decision, not a gap."""
    teammate = make_teammate()
    teammate.set_identity(
        "Léa", "Chen", Department.CUSTOMER_SERVICE, "lea-chen", OrgLevel.COMOP
    )
    use_case, repo, _ = build([make_manager(), teammate])

    await use_case.execute(
        command(
            first_name=None,
            last_name=None,
            department=None,
            github_username=None,
            org_level=None,
        )
    )

    stored = await repo.get_by_id(2)
    assert stored is not None
    assert stored.first_name is None
    assert stored.last_name is None
    assert stored.department is None
    assert stored.github_username is None
    assert stored.org_level is None


async def test_a_teammate_cannot_rewrite_a_colleague() -> None:
    use_case, _, _ = build([make_manager(), make_teammate()])

    with pytest.raises(ForbiddenActionError):
        await use_case.execute(command(actor_id=2, target_user_id=1))


async def test_an_unknown_teammate_is_rejected() -> None:
    use_case, _, _ = build([make_manager()])

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(command(target_user_id=99))


async def test_an_unknown_actor_is_rejected() -> None:
    use_case, _, _ = build([make_teammate()])

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(command(actor_id=99, target_user_id=2))


async def test_the_change_is_traced() -> None:
    use_case, _, audit = build([make_manager(), make_teammate()])

    await use_case.execute(command())

    trace = audit.logs[-1]
    assert trace.action is AuditAction.USER_IDENTITY_UPDATE
    assert trace.actor_id == 1
    assert trace.target_user_id == 2
    assert trace.payload == {
        "first_name": "Léa",
        "last_name": "Chen",
        "department": "customer_service",
        "github_username": "lea-chen",
        "org_level": "comop",
    }
