"""Saying how often one is written to. One's own mailbox, and no other."""

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.users.application.dtos.user_dto import ChooseOwnReminderCadenceCommand
from src.modules.users.application.use_cases.choose_own_reminder_cadence import (
    ChooseOwnReminderCadenceUseCase,
)
from src.modules.users.domain.entities.reminder_cadence import ReminderCadence
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
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
        ChooseOwnReminderCadenceUseCase(users=people, audit_logs=audit),
        people,
        audit,
    )


async def test_a_teammate_asks_for_the_weekly_letter() -> None:
    use_case, people, _ = build([a_teammate()])

    chosen = await use_case.execute(
        ChooseOwnReminderCadenceCommand(actor_id=2, cadence=ReminderCadence.WEEKLY)
    )

    assert chosen.reminder_cadence is ReminderCadence.WEEKLY
    stored = await people.get_by_id(2)
    assert stored is not None
    assert stored.reminder_cadence is ReminderCadence.WEEKLY


async def test_a_teammate_asks_for_no_letter_at_all() -> None:
    use_case, people, _ = build([a_teammate()])

    await use_case.execute(
        ChooseOwnReminderCadenceCommand(actor_id=2, cadence=ReminderCadence.NEVER)
    )

    stored = await people.get_by_id(2)
    assert stored is not None
    assert stored.reminder_cadence is ReminderCadence.NEVER


async def test_a_cadence_is_written_for_the_one_who_chose_it() -> None:
    # The command carries no target: there is no colleague's mailbox to reach.
    use_case, _, _ = build([a_teammate()])

    chosen = await use_case.execute(
        ChooseOwnReminderCadenceCommand(actor_id=2, cadence=ReminderCadence.NEVER)
    )

    assert chosen.id == 2


async def test_choosing_a_cadence_is_traced() -> None:
    use_case, _, audit = build([a_teammate()])

    await use_case.execute(
        ChooseOwnReminderCadenceCommand(actor_id=2, cadence=ReminderCadence.WEEKLY)
    )

    logged = audit.logs[-1]
    assert logged.action is AuditAction.USER_REMINDER_CHOOSE
    assert logged.actor_id == 2
    assert logged.target_user_id == 2
    assert logged.payload["cadence"] == "WEEKLY"


async def test_an_unknown_actor_chooses_nothing() -> None:
    use_case, _, _ = build([])

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(
            ChooseOwnReminderCadenceCommand(actor_id=2, cadence=ReminderCadence.NEVER)
        )


async def test_a_deactivated_account_chooses_nothing() -> None:
    use_case, _, _ = build([a_teammate(is_active=False)])

    with pytest.raises(ForbiddenActionError):
        await use_case.execute(
            ChooseOwnReminderCadenceCommand(actor_id=2, cadence=ReminderCadence.NEVER)
        )
