"""Provisionnement depuis Entra et gestion des roles."""

from datetime import datetime

import pytest

from src.modules.users.application.dtos.user_dto import (
    ChangeRoleCommand,
    EntraIdentity,
    SetUserActiveCommand,
)
from src.modules.users.application.use_cases.change_user_role import (
    ChangeUserRoleUseCase,
)
from src.modules.users.application.use_cases.provision_user import ProvisionUserUseCase
from src.modules.users.application.use_cases.set_user_active import SetUserActiveUseCase
from src.modules.users.domain.entities.user import Role, User
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


def build(users: list[User] | None = None):
    repo = InMemoryUserRepository(users if users is not None else [])
    audit = InMemoryAuditLogRepository()
    return (
        ProvisionUserUseCase(users=repo),
        ChangeUserRoleUseCase(users=repo, audit_logs=audit),
        repo,
        audit,
        SetUserActiveUseCase(users=repo, audit_logs=audit),
    )


async def test_an_unknown_identity_creates_a_teammate() -> None:
    provision, _, repo, _, _ = build()

    user = await provision.execute(
        EntraIdentity(oid="oid-new", email="d.dehe@waat.fr", display_name="D. Dehe")
    )

    assert user.id is not None
    assert user.role is Role.TEAMMATE
    assert len(await repo.list_all()) == 1


async def test_a_known_identity_is_reused() -> None:
    provision, _, repo, _, _ = build([make_teammate()])

    user = await provision.execute(
        EntraIdentity(
            oid="oid-teammate", email="l.chen@waat.fr", display_name="L. Chen"
        )
    )

    assert user.id == 2
    assert len(await repo.list_all()) == 1


async def test_a_seeded_user_keeps_their_role_on_first_login() -> None:
    """Le seed pre-attribue les roles avant la premiere connexion."""
    seeded = User(
        id=1,
        entra_oid=None,
        email="j.buget@waat.fr",
        display_name="J. Buget",
        role=Role.MANAGER,
    )
    provision, _, _, _, _ = build([seeded])

    user = await provision.execute(
        EntraIdentity(oid="oid-real", email="J.Buget@waat.fr", display_name="J. Buget")
    )

    assert user.id == 1
    assert user.role is Role.MANAGER
    assert user.entra_oid == "oid-real"


async def test_a_manager_promotes_a_teammate() -> None:
    _, change_role, repo, _, _ = build([make_manager(), make_teammate()])

    await change_role.execute(
        ChangeRoleCommand(actor_id=1, target_user_id=2, role=Role.MANAGER)
    )

    user = await repo.get_by_id(2)
    assert user is not None
    assert user.role is Role.MANAGER


async def test_a_teammate_cannot_promote_anyone() -> None:
    _, change_role, _, _, _ = build([make_manager(), make_teammate()])

    with pytest.raises(ForbiddenActionError):
        await change_role.execute(
            ChangeRoleCommand(actor_id=2, target_user_id=2, role=Role.MANAGER)
        )


async def test_a_role_change_is_traced() -> None:
    _, change_role, _, audit, _ = build([make_manager(), make_teammate()])

    await change_role.execute(
        ChangeRoleCommand(actor_id=1, target_user_id=2, role=Role.MANAGER)
    )

    log = audit.logs[-1]
    assert log.action.value == "user.role_change"
    assert (log.old_value, log.new_value) == ("TEAMMATE", "MANAGER")


async def test_a_new_user_is_stamped_with_their_first_connection() -> None:
    provision, _, _, _, _ = build()

    user = await provision.execute(
        EntraIdentity(oid="oid-new", email="d.dehe@waat.fr", display_name="D. Dehe"),
        now=datetime(2026, 9, 17, 9, 0),
    )

    assert user.last_login_at == datetime(2026, 9, 17, 9, 0)


async def test_a_returning_user_sees_their_connection_refreshed() -> None:
    teammate = make_teammate()
    teammate.last_login_at = datetime(2026, 9, 16, 9, 0)
    provision, _, repo, _, _ = build([teammate])

    await provision.execute(
        EntraIdentity(
            oid="oid-teammate", email="l.chen@waat.fr", display_name="L. Chen"
        ),
        now=datetime(2026, 9, 17, 9, 0),
    )

    stored = await repo.get_by_id(2)
    assert stored is not None
    assert stored.last_login_at == datetime(2026, 9, 17, 9, 0)


async def test_a_busy_user_is_not_written_on_every_request() -> None:
    """Le jeton est represente a chaque appel : la base n'a pas a le subir."""
    teammate = make_teammate()
    teammate.last_login_at = datetime(2026, 9, 17, 9, 0)
    provision, _, repo, _, _ = build([teammate])

    identity = EntraIdentity(
        oid="oid-teammate", email="l.chen@waat.fr", display_name="L. Chen"
    )
    await provision.execute(identity, now=datetime(2026, 9, 17, 9, 1))
    await provision.execute(identity, now=datetime(2026, 9, 17, 9, 2))

    assert repo.updates == 0


async def test_a_manager_deactivates_a_teammate() -> None:
    _, _, repo, _, set_active = build([make_manager(), make_teammate()])

    await set_active.execute(
        SetUserActiveCommand(actor_id=1, target_user_id=2, is_active=False)
    )

    user = await repo.get_by_id(2)
    assert user is not None
    assert user.is_active is False


async def test_a_manager_reactivates_a_teammate() -> None:
    teammate = make_teammate()
    teammate.is_active = False
    _, _, repo, _, set_active = build([make_manager(), teammate])

    await set_active.execute(
        SetUserActiveCommand(actor_id=1, target_user_id=2, is_active=True)
    )

    user = await repo.get_by_id(2)
    assert user is not None
    assert user.is_active is True


async def test_a_teammate_cannot_deactivate_anyone() -> None:
    _, _, _, _, set_active = build([make_manager(), make_teammate()])

    with pytest.raises(ForbiddenActionError):
        await set_active.execute(
            SetUserActiveCommand(actor_id=2, target_user_id=1, is_active=False)
        )


async def test_a_manager_cannot_deactivate_themselves() -> None:
    """Sinon le compte est refuse a la porte des la requete suivante."""
    _, _, repo, _, set_active = build([make_manager(), make_teammate()])

    with pytest.raises(ForbiddenActionError):
        await set_active.execute(
            SetUserActiveCommand(actor_id=1, target_user_id=1, is_active=False)
        )

    manager = await repo.get_by_id(1)
    assert manager is not None
    assert manager.is_active is True


async def test_a_manager_can_always_reactivate_themselves_is_pointless_but_allowed() -> (
    None
):
    """Reactiver n'enferme personne dehors : la regle ne vise que la coupure."""
    _, _, repo, _, set_active = build([make_manager(), make_teammate()])

    await set_active.execute(
        SetUserActiveCommand(actor_id=1, target_user_id=1, is_active=True)
    )

    manager = await repo.get_by_id(1)
    assert manager is not None
    assert manager.is_active is True


async def test_deactivating_an_unknown_user_is_refused() -> None:
    _, _, _, _, set_active = build([make_manager()])

    with pytest.raises(EntityNotFoundError):
        await set_active.execute(
            SetUserActiveCommand(actor_id=1, target_user_id=99, is_active=False)
        )


async def test_a_deactivation_is_traced() -> None:
    _, _, _, audit, set_active = build([make_manager(), make_teammate()])

    await set_active.execute(
        SetUserActiveCommand(actor_id=1, target_user_id=2, is_active=False)
    )

    log = audit.logs[-1]
    assert log.action.value == "user.deactivate"
    assert (log.old_value, log.new_value) == ("True", "False")


async def test_a_reactivation_is_traced_under_its_own_action() -> None:
    teammate = make_teammate()
    teammate.is_active = False
    _, _, _, audit, set_active = build([make_manager(), teammate])

    await set_active.execute(
        SetUserActiveCommand(actor_id=1, target_user_id=2, is_active=True)
    )

    log = audit.logs[-1]
    assert log.action.value == "user.activate"


async def test_setting_the_state_it_already_has_traces_nothing() -> None:
    """Un clic sans effet ne doit pas polluer le journal."""
    _, _, _, audit, set_active = build([make_manager(), make_teammate()])

    await set_active.execute(
        SetUserActiveCommand(actor_id=1, target_user_id=2, is_active=True)
    )

    assert audit.logs == []
