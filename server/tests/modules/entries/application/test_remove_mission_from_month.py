"""Removing a whole mission from a month."""

from datetime import date

import pytest

from src.modules.entries.application.dtos.set_entry_dto import RemoveMissionCommand
from src.modules.entries.application.use_cases.remove_mission_from_month import (
    RemoveMissionFromMonthUseCase,
)
from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.months.domain.entities.month import Month
from src.modules.projects.domain.entities.project import ProjectStatus
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryEntryRepository,
    InMemoryMonthRepository,
    InMemoryUserMissionRepository,
    InMemoryUserRepository,
)

ALICE = User(
    id=1,
    entra_oid="oid-1",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)
MONTH = date(2026, 9, 1)


def build(
    entries: list[Entry] | None = None,
    months: list[Month] | None = None,
    declared: list[tuple[int, int, date]] | None = None,
):
    users = InMemoryUserRepository([ALICE])
    entry_repo = InMemoryEntryRepository(entries or [])
    audit = InMemoryAuditLogRepository()
    rows = InMemoryUserMissionRepository(declared or [])
    use_case = RemoveMissionFromMonthUseCase(
        users=users,
        entries=entry_repo,
        months=InMemoryMonthRepository(months or []),
        audit_logs=audit,
        user_missions=rows,
    )
    return use_case, entry_repo, audit, rows


def an_entry(
    day: int, value: float = 1.0, project_id: int = 10, entry_id: int = 1
) -> Entry:
    return Entry(
        id=entry_id,
        user_id=1,
        project_id=project_id,
        day=date(2026, 9, day),
        value=DayValue(value),
        status_at_entry=ProjectStatus.SCOPING,
    )


def a_command(project_id: int = 10) -> RemoveMissionCommand:
    return RemoveMissionCommand(
        actor_id=1, target_user_id=1, project_id=project_id, month=MONTH
    )


async def test_every_entry_of_the_mission_is_removed() -> None:
    use_case, entries, _, _ = build(
        [an_entry(14, entry_id=1), an_entry(15, value=0.5, entry_id=2)]
    )

    await use_case.execute(a_command())

    assert await entries.list_for_month(1, MONTH) == []


async def test_the_other_missions_of_the_month_are_left_alone() -> None:
    other = an_entry(14, project_id=11, entry_id=2)
    use_case, entries, _, _ = build([an_entry(14, entry_id=1), other])

    await use_case.execute(a_command())

    assert await entries.list_for_month(1, MONTH) == [other]


async def test_the_removed_days_are_counted_back() -> None:
    """The screen announces what will be lost: the count must come from the domain."""
    use_case, _, _, _ = build([an_entry(14), an_entry(15, value=0.5, entry_id=2)])

    assert await use_case.execute(a_command()) == 1.5


async def test_removing_a_mission_without_entries_is_harmless() -> None:
    use_case, _, audit, _ = build()

    assert await use_case.execute(a_command()) == 0
    assert audit.logs == []


async def test_each_removal_is_traced_with_its_previous_value() -> None:
    use_case, _, audit, _ = build([an_entry(14), an_entry(15, value=0.5, entry_id=2)])

    await use_case.execute(a_command())

    assert [log.action.value for log in audit.logs] == ["entry.clear", "entry.clear"]
    assert sorted(log.old_value for log in audit.logs) == ["0.5", "1.0"]


async def test_a_validated_month_refuses_the_removal() -> None:
    month = Month(user_id=1, month=MONTH)
    month.validate(by=ALICE)
    use_case, entries, _, _ = build([an_entry(14)], months=[month])

    with pytest.raises(ForbiddenActionError):
        await use_case.execute(a_command())

    assert len(await entries.list_for_month(1, MONTH)) == 1


async def test_an_unknown_actor_is_refused() -> None:
    use_case, _, _, _ = build([an_entry(14)])

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(
            RemoveMissionCommand(
                actor_id=99, target_user_id=1, project_id=10, month=MONTH
            )
        )


async def test_the_mission_is_taken_off_the_month() -> None:
    """A row lined up but still empty must go for good, not come back reloaded."""
    use_case, _, _, rows = build(declared=[(1, 10, MONTH)])

    await use_case.execute(a_command())

    assert await rows.list_for_month(1, MONTH) == []


async def test_taking_a_mission_off_leaves_the_other_rows_of_the_month() -> None:
    use_case, _, _, rows = build(declared=[(1, 10, MONTH), (1, 11, MONTH)])

    await use_case.execute(a_command())

    assert await rows.list_for_month(1, MONTH) == [11]


async def test_a_validated_month_keeps_its_rows() -> None:
    month = Month(user_id=1, month=MONTH)
    month.validate(by=ALICE)
    use_case, _, _, rows = build(months=[month], declared=[(1, 10, MONTH)])

    with pytest.raises(ForbiddenActionError):
        await use_case.execute(a_command())

    assert await rows.list_for_month(1, MONTH) == [10]
