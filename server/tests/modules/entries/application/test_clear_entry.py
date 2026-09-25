"""Deleting an entry."""

from datetime import date

import pytest

from src.modules.entries.application.dtos.set_entry_dto import (
    ClearEntryCommand,
    SetEntryCommand,
)
from src.modules.entries.application.use_cases.clear_entry import ClearEntryUseCase
from src.modules.entries.application.use_cases.set_entry import SetEntryUseCase
from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.months.domain.entities.month import Month
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.projects.domain.entities.activity import Activity
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.enums.work_nature import WorkNature
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)
from tests.helpers.in_memory_repositories import (
    InMemoryActivityRepository,
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
PROJECT = Project(
    id=10, label="Portail", kind=ProjectKind.PROJECT, status=ProjectStatus.SCOPING
)
DAY = date(2026, 9, 15)


#: A project is declared on through one of its activities, never directly.
DEV = Activity(
    id=100,
    project_id=10,
    label="Développement",
    nature=WorkNature.DEVELOPMENT,
)


def build(entries: list[Entry] | None = None, months: list[Month] | None = None):
    users = InMemoryUserRepository([ALICE])
    entry_repo = InMemoryEntryRepository(entries or [])
    month_repo = InMemoryMonthRepository(months or [])
    audit = InMemoryAuditLogRepository()
    clear = ClearEntryUseCase(
        users=users,
        entries=entry_repo,
        months=month_repo,
        audit_logs=audit,
        notifications=NotificationDelivery(InMemoryNotificationRepository()),
    )
    set_entry = SetEntryUseCase(
        users=users,
        projects=InMemoryProjectRepository([PROJECT]),
        activities=InMemoryActivityRepository([DEV]),
        entries=entry_repo,
        months=month_repo,
        audit_logs=audit,
        notifications=NotificationDelivery(InMemoryNotificationRepository()),
    )
    return clear, set_entry, entry_repo, audit


def an_entry(day: date = DAY, value: float = 1.0) -> Entry:
    return Entry(
        id=1,
        user_id=1,
        project_id=10,
        activity_id=100,
        day=day,
        value=DayValue(value),
        status_at_entry=ProjectStatus.SCOPING,
    )


async def test_an_entry_is_removed() -> None:
    clear, _, entries, _ = build([an_entry()])

    await clear.execute(
        ClearEntryCommand(
            actor_id=1, target_user_id=1, project_id=10, activity_id=100, day=DAY
        )
    )

    assert await entries.get(1, 10, 100, DAY) is None


async def test_clearing_an_empty_cell_is_harmless() -> None:
    """The entry cycle passes back through empty: the operation must stay safe."""
    clear, _, entries, _ = build()

    await clear.execute(
        ClearEntryCommand(
            actor_id=1, target_user_id=1, project_id=10, activity_id=100, day=DAY
        )
    )

    assert await entries.get(1, 10, 100, DAY) is None


async def test_removal_is_traced_with_the_previous_value() -> None:
    clear, _, _, audit = build([an_entry(value=0.5)])

    await clear.execute(
        ClearEntryCommand(
            actor_id=1, target_user_id=1, project_id=10, activity_id=100, day=DAY
        )
    )

    log = audit.logs[-1]
    assert log.action.value == "entry.clear"
    assert log.old_value == "0.5"


async def test_clearing_an_empty_cell_leaves_no_trace() -> None:
    clear, _, _, audit = build()

    await clear.execute(
        ClearEntryCommand(
            actor_id=1, target_user_id=1, project_id=10, activity_id=100, day=DAY
        )
    )

    assert audit.logs == []


async def test_a_validated_month_refuses_removal() -> None:
    month = Month(user_id=1, month=date(2026, 9, 1))
    month.validate(by=ALICE)
    clear, _, entries, _ = build([an_entry()], months=[month])

    with pytest.raises(ForbiddenActionError):
        await clear.execute(
            ClearEntryCommand(
                actor_id=1, target_user_id=1, project_id=10, activity_id=100, day=DAY
            )
        )

    assert await entries.get(1, 10, 100, DAY) is not None


async def test_an_unknown_actor_is_rejected() -> None:
    clear, _, _, _ = build([an_entry()])

    with pytest.raises(EntityNotFoundError):
        await clear.execute(
            ClearEntryCommand(
                actor_id=99, target_user_id=1, project_id=10, activity_id=100, day=DAY
            )
        )


async def test_a_non_working_day_can_still_be_cleaned_up() -> None:
    """Entering on a Saturday is forbidden, removing an inherited entry never is."""
    saturday = date(2026, 9, 12)
    clear, _, entries, _ = build([an_entry(day=saturday)])

    await clear.execute(
        ClearEntryCommand(
            actor_id=1, target_user_id=1, project_id=10, activity_id=100, day=saturday
        )
    )

    assert await entries.get(1, 10, 100, saturday) is None


async def test_a_full_cycle_returns_the_cell_to_empty() -> None:
    """Empty -> half -> full -> empty: the full round of the click."""
    clear, set_entry, entries, _ = build()
    for value in (0.5, 1.0):
        await set_entry.execute(
            SetEntryCommand(
                actor_id=1,
                target_user_id=1,
                project_id=10,
                activity_id=100,
                day=DAY,
                value=value,
            )
        )

    await clear.execute(
        ClearEntryCommand(
            actor_id=1, target_user_id=1, project_id=10, activity_id=100, day=DAY
        )
    )

    assert await entries.get(1, 10, 100, DAY) is None
