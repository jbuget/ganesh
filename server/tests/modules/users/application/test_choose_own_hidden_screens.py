"""Arranging one's own sidebar. One's own bar, and no other."""

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.users.application.dtos.user_dto import ChooseOwnHiddenScreensCommand
from src.modules.users.application.use_cases.choose_own_hidden_screens import (
    ChooseOwnHiddenScreensUseCase,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
    ValidationError,
)
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryUserRepository,
)


def a_teammate(is_active: bool = True) -> User:
    return User(
        id=2,
        entra_oid="oid-teammate",
        email="l.chen@waat.fr",
        display_name="L. Chen",
        role=Role.TEAMMATE,
        is_active=is_active,
    )


def build(users: list[User]):
    people = InMemoryUserRepository(users)
    audit = InMemoryAuditLogRepository()
    return (
        ChooseOwnHiddenScreensUseCase(users=people, audit_logs=audit),
        people,
        audit,
    )


async def test_a_teammate_hides_the_screens_they_never_open() -> None:
    use_case, people, _ = build([a_teammate()])

    chosen = await use_case.execute(
        ChooseOwnHiddenScreensCommand(actor_id=2, screens=["/stats", "/logs"])
    )

    assert chosen.hidden_screens == ("/logs", "/stats")
    stored = await people.get_by_id(2)
    assert stored is not None
    assert stored.hidden_screens == ("/logs", "/stats")


async def test_a_bar_is_written_for_the_one_who_arranged_it() -> None:
    # The command carries no target: there is no colleague's bar to reach.
    use_case, _, _ = build([a_teammate()])

    chosen = await use_case.execute(
        ChooseOwnHiddenScreensCommand(actor_id=2, screens=[])
    )

    assert chosen.id == 2


async def test_arranging_the_bar_is_traced() -> None:
    use_case, _, audit = build([a_teammate()])

    await use_case.execute(
        ChooseOwnHiddenScreensCommand(actor_id=2, screens=["/stats"])
    )

    logged = audit.logs[-1]
    assert logged.action is AuditAction.USER_NAVIGATION_CHOOSE
    assert logged.actor_id == 2
    assert logged.target_user_id == 2
    assert logged.payload["hidden_screens"] == ["/stats"]


async def test_a_refused_list_is_neither_stored_nor_traced() -> None:
    use_case, people, audit = build([a_teammate()])

    with pytest.raises(ValidationError):
        await use_case.execute(ChooseOwnHiddenScreensCommand(actor_id=2, screens=["/"]))

    stored = await people.get_by_id(2)
    assert stored is not None
    assert stored.hidden_screens == ()
    assert audit.logs == []


async def test_an_unknown_actor_arranges_nothing() -> None:
    use_case, _, _ = build([])

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(ChooseOwnHiddenScreensCommand(actor_id=2, screens=[]))


async def test_a_deactivated_account_arranges_nothing() -> None:
    use_case, _, _ = build([a_teammate(is_active=False)])

    with pytest.raises(ForbiddenActionError):
        await use_case.execute(ChooseOwnHiddenScreensCommand(actor_id=2, screens=[]))
