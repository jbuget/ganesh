"""Recording a time entry."""

from datetime import date

import pytest

from src.modules.entries.application.dtos.set_entry_dto import SetEntryCommand
from src.modules.entries.application.use_cases.set_entry import SetEntryUseCase
from src.modules.months.domain.entities.month import Month
from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
    ValidationError,
)
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryEntryRepository,
    InMemoryMonthRepository,
    InMemoryNotificationRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
)

ALICE = User(
    id=1,
    entra_oid="oid-1",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)
BOB = User(
    id=2,
    entra_oid="oid-2",
    email="g.belhadj@waat.fr",
    display_name="G. Belhadj",
    role=Role.TEAMMATE,
)
PROJECT = Project(
    id=10,
    label="Portail bailleurs",
    kind=ProjectKind.PROJECT,
    status=ProjectStatus.SCOPING,
)
DAY = date(2026, 9, 15)


def build(months: list[Month] | None = None):
    users = InMemoryUserRepository([ALICE, BOB])
    projects = InMemoryProjectRepository([PROJECT])
    entries = InMemoryEntryRepository()
    month_repo = InMemoryMonthRepository(months or [])
    audit = InMemoryAuditLogRepository()
    inbox = InMemoryNotificationRepository()
    use_case = SetEntryUseCase(
        users=users,
        projects=projects,
        entries=entries,
        months=month_repo,
        audit_logs=audit,
        notifications=NotificationDelivery(inbox),
    )
    return use_case, entries, audit, month_repo, inbox


async def test_a_user_records_time_on_their_own_month() -> None:
    use_case, entries, _, _, _ = build()

    await use_case.execute(
        SetEntryCommand(actor_id=1, target_user_id=1, project_id=10, day=DAY, value=0.5)
    )

    saved = await entries.get(1, 10, DAY)
    assert saved is not None
    assert saved.value == 0.5


async def test_the_entry_captures_the_current_project_phase() -> None:
    use_case, entries, _, _, _ = build()

    await use_case.execute(
        SetEntryCommand(actor_id=1, target_user_id=1, project_id=10, day=DAY, value=1.0)
    )

    saved = await entries.get(1, 10, DAY)
    assert saved is not None
    assert saved.status_at_entry is ProjectStatus.SCOPING


async def test_a_user_can_record_time_on_a_colleague_open_month() -> None:
    """Transparency is deliberate: anyone may fix another's open month."""
    use_case, entries, _, _, _ = build()

    await use_case.execute(
        SetEntryCommand(actor_id=1, target_user_id=2, project_id=10, day=DAY, value=1.0)
    )

    assert await entries.get(2, 10, DAY) is not None


async def test_writing_to_a_validated_month_is_rejected() -> None:
    month = Month(user_id=1, month=date(2026, 9, 1))
    month.validate(by=ALICE)
    use_case, entries, _, _, _ = build(months=[month])

    with pytest.raises(ForbiddenActionError):
        await use_case.execute(
            SetEntryCommand(
                actor_id=1, target_user_id=1, project_id=10, day=DAY, value=1.0
            )
        )

    assert await entries.get(1, 10, DAY) is None


async def test_a_saturday_is_rejected() -> None:
    """The rule lives in the domain: the API refuses, whoever the caller is."""
    use_case, entries, _, _, _ = build()

    with pytest.raises(ValidationError):
        await use_case.execute(
            SetEntryCommand(
                actor_id=1,
                target_user_id=1,
                project_id=10,
                day=date(2026, 9, 12),
                value=1.0,
            )
        )

    assert await entries.get(1, 10, date(2026, 9, 12)) is None


async def test_a_public_holiday_is_rejected() -> None:
    use_case, _, _, _, _ = build()

    with pytest.raises(ValidationError):
        await use_case.execute(
            SetEntryCommand(
                actor_id=1,
                target_user_id=1,
                project_id=10,
                day=date(2026, 5, 1),
                value=1.0,
            )
        )


async def test_a_rejected_day_leaves_no_trace_in_the_audit_log() -> None:
    use_case, _, audit, _, _ = build()

    with pytest.raises(ValidationError):
        await use_case.execute(
            SetEntryCommand(
                actor_id=1,
                target_user_id=1,
                project_id=10,
                day=date(2026, 9, 13),
                value=1.0,
            )
        )

    assert audit.logs == []


async def test_an_invalid_value_is_rejected() -> None:
    use_case, _, _, _, _ = build()

    with pytest.raises(ValidationError):
        await use_case.execute(
            SetEntryCommand(
                actor_id=1, target_user_id=1, project_id=10, day=DAY, value=0.8
            )
        )


async def test_an_unknown_project_is_rejected() -> None:
    use_case, _, _, _, _ = build()

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(
            SetEntryCommand(
                actor_id=1, target_user_id=1, project_id=999, day=DAY, value=1.0
            )
        )


async def test_setting_a_value_twice_overwrites_it() -> None:
    use_case, entries, _, _, _ = build()
    command = SetEntryCommand(
        actor_id=1, target_user_id=1, project_id=10, day=DAY, value=0.5
    )
    await use_case.execute(command)

    await use_case.execute(
        SetEntryCommand(actor_id=1, target_user_id=1, project_id=10, day=DAY, value=1.0)
    )

    saved = await entries.get(1, 10, DAY)
    assert saved is not None
    assert saved.value == 1.0
    assert len(await entries.list_for_month(1, DAY)) == 1


async def test_every_entry_is_traced() -> None:
    use_case, _, audit, _, _ = build()

    await use_case.execute(
        SetEntryCommand(actor_id=1, target_user_id=2, project_id=10, day=DAY, value=1.0)
    )

    assert len(audit.logs) == 1
    log = audit.logs[0]
    assert log.actor_id == 1
    assert log.target_user_id == 2
    assert log.new_value == "1.0"
    assert log.is_on_behalf_of_someone_else is True


async def test_overwriting_traces_the_previous_value() -> None:
    use_case, _, audit, _, _ = build()
    base = SetEntryCommand(
        actor_id=1, target_user_id=1, project_id=10, day=DAY, value=0.5
    )
    await use_case.execute(base)

    await use_case.execute(
        SetEntryCommand(actor_id=1, target_user_id=1, project_id=10, day=DAY, value=1.0)
    )

    assert audit.logs[-1].old_value == "0.5"
    assert audit.logs[-1].new_value == "1.0"


async def test_recording_time_opens_the_month_implicitly() -> None:
    use_case, _, _, months, _ = build()

    await use_case.execute(
        SetEntryCommand(actor_id=1, target_user_id=1, project_id=10, day=DAY, value=1.0)
    )

    month = await months.get(1, date(2026, 9, 1))
    assert month is not None
    assert month.is_writable is True


async def test_an_inactive_user_cannot_record_time() -> None:
    use_case, _, _, _, _ = build()
    ALICE.is_active = False

    try:
        with pytest.raises(ForbiddenActionError):
            await use_case.execute(
                SetEntryCommand(
                    actor_id=1, target_user_id=1, project_id=10, day=DAY, value=1.0
                )
            )
    finally:
        ALICE.is_active = True


async def test_writing_on_a_colleagues_month_tells_them() -> None:
    use_case, _, _, _, inbox = build()

    await use_case.execute(
        SetEntryCommand(actor_id=2, target_user_id=1, project_id=10, day=DAY, value=0.5)
    )

    [told] = inbox.notifications
    assert told.recipient_id == 1
    assert told.actor_id == 2
    assert told.kind is NotificationKind.TIMESHEET_EDITED
    # The month, not the day: it is what folds a whole month's edits into one.
    assert told.day == date(2026, 9, 1)


async def test_a_month_filled_in_cell_by_cell_rings_once() -> None:
    use_case, _, _, _, inbox = build()

    for day in (date(2026, 9, 15), date(2026, 9, 16), date(2026, 9, 17)):
        await use_case.execute(
            SetEntryCommand(
                actor_id=2, target_user_id=1, project_id=10, day=day, value=0.5
            )
        )

    [told] = inbox.notifications
    assert told.count == 3


async def test_writing_on_ones_own_month_rings_nowhere() -> None:
    use_case, _, _, _, inbox = build()

    await use_case.execute(
        SetEntryCommand(actor_id=1, target_user_id=1, project_id=10, day=DAY, value=0.5)
    )

    assert inbox.notifications == []
