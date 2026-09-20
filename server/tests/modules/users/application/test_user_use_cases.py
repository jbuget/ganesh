"""Provisioning from Entra and managing roles."""

from datetime import datetime

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.domain.services.delivery import NotificationDelivery
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
    InMemoryNotificationRepository,
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
    inbox = InMemoryNotificationRepository()
    delivery = NotificationDelivery(inbox)
    return (
        ProvisionUserUseCase(users=repo, audit_logs=audit),
        ChangeUserRoleUseCase(users=repo, audit_logs=audit, notifications=delivery),
        repo,
        audit,
        SetUserActiveUseCase(users=repo, audit_logs=audit, notifications=delivery),
        inbox,
    )


async def test_an_unknown_identity_creates_a_teammate() -> None:
    provision, _, repo, _, _, _ = build()

    user = await provision.execute(
        EntraIdentity(oid="oid-new", email="d.dehe@waat.fr", display_name="D. Dehe")
    )

    assert user.id is not None
    assert user.role is Role.TEAMMATE
    assert len(await repo.list_all()) == 1


async def test_a_known_identity_is_reused() -> None:
    provision, _, repo, _, _, _ = build([make_teammate()])

    user = await provision.execute(
        EntraIdentity(
            oid="oid-teammate", email="l.chen@waat.fr", display_name="L. Chen"
        )
    )

    assert user.id == 2
    assert len(await repo.list_all()) == 1


async def test_a_seeded_user_keeps_their_role_on_first_login() -> None:
    """The seed pre-assigns roles before the first login."""
    seeded = User(
        id=1,
        entra_oid=None,
        email="j.buget@waat.fr",
        display_name="J. Buget",
        role=Role.MANAGER,
    )
    provision, _, _, _, _, _ = build([seeded])

    user = await provision.execute(
        EntraIdentity(oid="oid-real", email="J.Buget@waat.fr", display_name="J. Buget")
    )

    assert user.id == 1
    assert user.role is Role.MANAGER
    assert user.entra_oid == "oid-real"


async def test_a_manager_promotes_a_teammate() -> None:
    _, change_role, repo, _, _, _ = build([make_manager(), make_teammate()])

    await change_role.execute(
        ChangeRoleCommand(actor_id=1, target_user_id=2, role=Role.MANAGER)
    )

    user = await repo.get_by_id(2)
    assert user is not None
    assert user.role is Role.MANAGER


async def test_a_teammate_cannot_promote_anyone() -> None:
    _, change_role, _, _, _, _ = build([make_manager(), make_teammate()])

    with pytest.raises(ForbiddenActionError):
        await change_role.execute(
            ChangeRoleCommand(actor_id=2, target_user_id=2, role=Role.MANAGER)
        )


async def test_a_role_change_is_traced() -> None:
    _, change_role, _, audit, _, _ = build([make_manager(), make_teammate()])

    await change_role.execute(
        ChangeRoleCommand(actor_id=1, target_user_id=2, role=Role.MANAGER)
    )

    log = audit.logs[-1]
    assert log.action.value == "user.role_change"
    assert (log.old_value, log.new_value) == ("TEAMMATE", "MANAGER")


async def test_a_new_user_is_stamped_with_their_first_connection() -> None:
    provision, _, _, _, _, _ = build()

    user = await provision.execute(
        EntraIdentity(oid="oid-new", email="d.dehe@waat.fr", display_name="D. Dehe"),
        now=datetime(2026, 9, 17, 9, 0),
    )

    assert user.last_login_at == datetime(2026, 9, 17, 9, 0)


async def test_a_returning_user_sees_their_connection_refreshed() -> None:
    teammate = make_teammate()
    teammate.last_login_at = datetime(2026, 9, 16, 9, 0)
    provision, _, repo, _, _, _ = build([teammate])

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
    """The token is presented on every call: the database need not suffer it."""
    teammate = make_teammate()
    teammate.last_login_at = datetime(2026, 9, 17, 9, 0)
    provision, _, repo, _, _, _ = build([teammate])

    identity = EntraIdentity(
        oid="oid-teammate", email="l.chen@waat.fr", display_name="L. Chen"
    )
    await provision.execute(identity, now=datetime(2026, 9, 17, 9, 1))
    await provision.execute(identity, now=datetime(2026, 9, 17, 9, 2))

    assert repo.updates == 0


async def test_a_manager_deactivates_a_teammate() -> None:
    _, _, repo, _, set_active, _ = build([make_manager(), make_teammate()])

    await set_active.execute(
        SetUserActiveCommand(actor_id=1, target_user_id=2, is_active=False)
    )

    user = await repo.get_by_id(2)
    assert user is not None
    assert user.is_active is False


async def test_a_manager_reactivates_a_teammate() -> None:
    teammate = make_teammate()
    teammate.is_active = False
    _, _, repo, _, set_active, _ = build([make_manager(), teammate])

    await set_active.execute(
        SetUserActiveCommand(actor_id=1, target_user_id=2, is_active=True)
    )

    user = await repo.get_by_id(2)
    assert user is not None
    assert user.is_active is True


async def test_a_teammate_cannot_deactivate_anyone() -> None:
    _, _, _, _, set_active, _ = build([make_manager(), make_teammate()])

    with pytest.raises(ForbiddenActionError):
        await set_active.execute(
            SetUserActiveCommand(actor_id=2, target_user_id=1, is_active=False)
        )


async def test_a_manager_cannot_deactivate_themselves() -> None:
    """Otherwise the account is turned away at the door on the next request."""
    _, _, repo, _, set_active, _ = build([make_manager(), make_teammate()])

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
    """Reactivating locks nobody out: the rule only aims at cutting off."""
    _, _, repo, _, set_active, _ = build([make_manager(), make_teammate()])

    await set_active.execute(
        SetUserActiveCommand(actor_id=1, target_user_id=1, is_active=True)
    )

    manager = await repo.get_by_id(1)
    assert manager is not None
    assert manager.is_active is True


async def test_deactivating_an_unknown_user_is_refused() -> None:
    _, _, _, _, set_active, _ = build([make_manager()])

    with pytest.raises(EntityNotFoundError):
        await set_active.execute(
            SetUserActiveCommand(actor_id=1, target_user_id=99, is_active=False)
        )


async def test_a_deactivation_is_traced() -> None:
    _, _, _, audit, set_active, _ = build([make_manager(), make_teammate()])

    await set_active.execute(
        SetUserActiveCommand(actor_id=1, target_user_id=2, is_active=False)
    )

    log = audit.logs[-1]
    assert log.action.value == "user.deactivate"
    assert (log.old_value, log.new_value) == ("True", "False")


async def test_a_reactivation_is_traced_under_its_own_action() -> None:
    teammate = make_teammate()
    teammate.is_active = False
    _, _, _, audit, set_active, _ = build([make_manager(), teammate])

    await set_active.execute(
        SetUserActiveCommand(actor_id=1, target_user_id=2, is_active=True)
    )

    log = audit.logs[-1]
    assert log.action.value == "user.activate"


async def test_setting_the_state_it_already_has_traces_nothing() -> None:
    """A click with no effect must not clutter the log."""
    _, _, _, audit, set_active, _ = build([make_manager(), make_teammate()])

    await set_active.execute(
        SetUserActiveCommand(actor_id=1, target_user_id=2, is_active=True)
    )

    assert audit.logs == []


async def test_an_account_coming_into_being_is_traced() -> None:
    provision, _, repo, audit, _, _ = build()

    user = await provision.execute(
        EntraIdentity(oid="oid-new", email="d.dehe@waat.fr", display_name="D. Dehe")
    )

    (trace,) = audit.logs
    assert trace.action is AuditAction.USER_CREATE
    assert (trace.actor_id, trace.target_user_id) == (user.id, user.id)
    assert trace.new_value == "d.dehe@waat.fr"


async def test_signing_in_again_traces_nothing() -> None:
    """A line per sign-in would bury the log under what nobody decided."""
    provision, _, _, audit, _, _ = build()
    identity = EntraIdentity(
        oid="oid-new", email="d.dehe@waat.fr", display_name="D. Dehe"
    )
    await provision.execute(identity)
    audit.logs.clear()

    await provision.execute(identity)

    assert audit.logs == []


async def test_a_teammate_hears_their_role_change() -> None:
    _, change_role, _, _, _, inbox = build([make_manager(), make_teammate()])

    await change_role.execute(
        ChangeRoleCommand(actor_id=1, target_user_id=2, role=Role.MANAGER)
    )

    [told] = inbox.notifications
    assert told.recipient_id == 2
    assert told.kind is NotificationKind.USER_ROLE_CHANGED
    assert told.payload == {"from": "TEAMMATE", "to": "MANAGER"}


async def test_a_teammate_hears_their_account_come_back() -> None:
    """A deactivated account cannot read: the line waits for the return."""
    _, _, _, _, set_active, inbox = build([make_manager(), make_teammate()])

    await set_active.execute(
        SetUserActiveCommand(actor_id=1, target_user_id=2, is_active=False)
    )
    await set_active.execute(
        SetUserActiveCommand(actor_id=1, target_user_id=2, is_active=True)
    )

    assert [told.kind for told in inbox.notifications] == [
        NotificationKind.USER_DEACTIVATED,
        NotificationKind.USER_ACTIVATED,
    ]
