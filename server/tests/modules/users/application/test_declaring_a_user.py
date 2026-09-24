"""Declaring an account before its owner has ever signed in."""

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.users.application.dtos.user_dto import (
    DeclareUserCommand,
    EntraIdentity,
)
from src.modules.users.application.use_cases.declare_user import DeclareUserUseCase
from src.modules.users.application.use_cases.provision_user import ProvisionUserUseCase
from src.modules.users.domain.entities.user import Role, User
from src.shared.enums.department import Department
from src.shared.exceptions.domain_exceptions import (
    ConflictError,
    ForbiddenActionError,
    ValidationError,
)
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryUserRepository,
)

ADMIN, MANAGER, TEAMMATE = 1, 2, 3


def make_team() -> list[User]:
    return [
        User(
            id=ADMIN,
            entra_oid="oid-admin",
            email="j.buget@waat.fr",
            display_name="J. Buget",
            role=Role.ADMIN,
        ),
        User(
            id=MANAGER,
            entra_oid="oid-manager",
            email="m.mina@waat.fr",
            display_name="M. Mina",
            role=Role.MANAGER,
        ),
        User(
            id=TEAMMATE,
            entra_oid="oid-teammate",
            email="l.chen@waat.fr",
            display_name="L. Chen",
            role=Role.TEAMMATE,
        ),
    ]


def build(users: list[User] | None = None):
    repo = InMemoryUserRepository(make_team() if users is None else users)
    audit = InMemoryAuditLogRepository()
    return DeclareUserUseCase(users=repo, audit_logs=audit), repo, audit


def command(actor_id: int = MANAGER, **overrides) -> DeclareUserCommand:
    fields: dict = {
        "actor_id": actor_id,
        "email": "n.arrivee@waat.fr",
        "first_name": "Nina",
        "last_name": "Arrivée",
        "role": Role.TEAMMATE,
    }
    fields.update(overrides)
    return DeclareUserCommand(**fields)


async def test_a_manager_declares_a_teammate_who_has_never_signed_in() -> None:
    declare, repo, _ = build()

    user = await declare.execute(command(department=Department.CUSTOMER_SERVICE))

    assert user.id is not None
    assert user.email == "n.arrivee@waat.fr"
    assert user.role is Role.TEAMMATE
    assert user.department is Department.CUSTOMER_SERVICE
    assert user.is_active is True
    # Nobody has signed in: no Entra id — « » is how the entity says it, and
    # the repository stores it as NULL — and no visit to date.
    assert user.entra_oid == ""
    assert user.last_login_at is None
    assert len(await repo.list_all()) == 4


async def test_the_declared_name_is_what_the_team_reads_until_entra_writes_one() -> (
    None
):
    declare, _, _ = build()

    user = await declare.execute(command())

    assert user.display_name == "Nina Arrivée"
    assert user.label == "Nina Arrivée"


async def test_the_account_is_claimed_on_the_first_sign_in() -> None:
    """The whole point of declaring: one account, not two."""
    declare, repo, audit = build()
    declared = await declare.execute(command(role=Role.MANAGER, actor_id=ADMIN))
    provision = ProvisionUserUseCase(users=repo, audit_logs=audit)

    user = await provision.execute(
        EntraIdentity(
            oid="oid-nina",
            # Whatever case Entra sends the address in.
            email="N.Arrivee@waat.fr",
            display_name="N. Arrivée",
        )
    )

    assert user.id == declared.id
    assert user.entra_oid == "oid-nina"
    # The rank given on declaring is what survives the first sign-in.
    assert user.role is Role.MANAGER
    assert len(await repo.list_all()) == 4


async def test_declaring_names_whoever_decided_it() -> None:
    """Where provisioning names the account itself, a decision names its author."""
    declare, _, audit = build()

    user = await declare.execute(command())

    line = audit.logs[-1]
    assert line.action is AuditAction.USER_CREATE
    assert line.actor_id == MANAGER
    assert line.target_user_id == user.id
    assert line.new_value == "n.arrivee@waat.fr"


async def test_an_admin_declares_an_admin() -> None:
    declare, _, _ = build()

    user = await declare.execute(command(actor_id=ADMIN, role=Role.ADMIN))

    assert user.role is Role.ADMIN


async def test_a_manager_cannot_declare_an_admin() -> None:
    """Nobody confers a rank above their own, creation included."""
    declare, repo, _ = build()

    with pytest.raises(ForbiddenActionError):
        await declare.execute(command(actor_id=MANAGER, role=Role.ADMIN))

    assert len(await repo.list_all()) == 3


async def test_a_teammate_declares_nobody() -> None:
    declare, repo, _ = build()

    with pytest.raises(ForbiddenActionError):
        await declare.execute(command(actor_id=TEAMMATE))

    assert len(await repo.list_all()) == 3


async def test_an_address_the_register_already_knows_is_refused() -> None:
    """Two accounts at one address and neither can be claimed."""
    declare, repo, _ = build()

    with pytest.raises(ConflictError):
        await declare.execute(command(email="L.Chen@waat.fr"))

    assert len(await repo.list_all()) == 3


async def test_declaring_somebody_is_saying_who_they_are() -> None:
    declare, _, _ = build()

    with pytest.raises(ValidationError):
        await declare.execute(command(first_name="  ", last_name="Arrivée"))
