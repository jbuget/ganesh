"""The register handed over for a window, in one go.

The grid answers one person's question — my month. This answers what the whole
team declared between two days, which is what payroll, invoicing or a dashboard
outside Ganesh comes to ask.
"""

from datetime import date

import pytest

from src.modules.entries.application.use_cases.export_entries import (
    MAX_EXPORT_DAYS,
    ExportEntriesUseCase,
)
from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.projects.domain.entities.activity import Activity
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.users.domain.entities.user import User
from src.shared.enums.work_nature import WorkNature
from src.shared.exceptions.domain_exceptions import ValidationError
from tests.helpers.in_memory_repositories import (
    InMemoryActivityRepository,
    InMemoryEntryRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
)

ALICE = User(id=1, entra_oid="oid-1", email="a@waat.fr", display_name="A. Ba")
BOB = User(id=2, entra_oid="oid-2", email="b@waat.fr", display_name="B. Cy")
EXTRANET = Project(id=7, label="Extranet", kind=ProjectKind.PROJECT)
LEAVE = Project(id=9, label="Congés", kind=ProjectKind.OFF_PROJECT, status=None)
DEV = Activity(
    id=70,
    project_id=7,
    label="Développement",
    nature=WorkNature.DEVELOPMENT,
)


def entry(
    user_id: int,
    project_id: int,
    day: date,
    value: float = 1.0,
    activity_id: int | None = None,
) -> Entry:
    return Entry(
        id=None,
        user_id=user_id,
        project_id=project_id,
        activity_id=activity_id,
        day=day,
        value=DayValue(value),
        status_at_entry=ProjectStatus.DEVELOPMENT,
    )


def use_case(entries: list[Entry]) -> ExportEntriesUseCase:
    return ExportEntriesUseCase(
        entries=InMemoryEntryRepository(entries),
        activities=InMemoryActivityRepository([DEV]),
        users=InMemoryUserRepository([ALICE, BOB]),
        projects=InMemoryProjectRepository([EXTRANET, LEAVE]),
    )


@pytest.mark.asyncio
async def test_a_window_hands_over_what_it_holds() -> None:
    rows = await use_case(
        [
            entry(1, 7, date(2026, 9, 14)),
            entry(2, 9, date(2026, 9, 15), 0.5),
        ]
    ).execute(date(2026, 9, 1), date(2026, 9, 30))

    assert [(row.user_id, row.project_id, row.value) for row in rows] == [
        (1, 7, 1.0),
        (2, 9, 0.5),
    ]


@pytest.mark.asyncio
async def test_a_day_outside_the_window_stays_out() -> None:
    rows = await use_case(
        [entry(1, 7, date(2026, 8, 31)), entry(1, 7, date(2026, 9, 1))]
    ).execute(date(2026, 9, 1), date(2026, 9, 30))

    assert [row.day for row in rows] == [date(2026, 9, 1)]


@pytest.mark.asyncio
async def test_both_ends_are_included() -> None:
    rows = await use_case(
        [entry(1, 7, date(2026, 9, 1)), entry(1, 7, date(2026, 9, 30))]
    ).execute(date(2026, 9, 1), date(2026, 9, 30))

    assert len(rows) == 2


@pytest.mark.asyncio
async def test_a_row_carries_the_names_that_make_it_readable() -> None:
    # An export is read once, by something with no other way of asking who
    # user 1 is. The ids stay so a second pull reconciles with the first.
    rows = await use_case([entry(1, 7, date(2026, 9, 14))]).execute(
        date(2026, 9, 1), date(2026, 9, 30)
    )

    assert rows[0].user_label == "A. Ba"
    assert rows[0].project_label == "Extranet"
    assert rows[0].status_at_entry is ProjectStatus.DEVELOPMENT


@pytest.mark.asyncio
async def test_a_window_that_ends_before_it_starts_is_refused() -> None:
    with pytest.raises(ValidationError):
        await use_case([]).execute(date(2026, 9, 30), date(2026, 9, 1))


@pytest.mark.asyncio
async def test_a_window_wider_than_a_year_is_refused() -> None:
    # A guard on a route a machine calls, so one mistyped date does not ask
    # for the whole history at once.
    start = date(2026, 1, 1)

    with pytest.raises(ValidationError):
        await use_case([]).execute(start, start.replace(year=2027, day=2))


@pytest.mark.asyncio
async def test_a_year_and_a_day_still_goes_through() -> None:
    start = date(2026, 1, 1)
    end = date.fromordinal(start.toordinal() + MAX_EXPORT_DAYS - 1)

    assert await use_case([]).execute(start, end) == []


async def test_a_row_says_which_trade_the_day_was_booked_under() -> None:
    """« On what » without « under which trade » is the question this level
    was added to answer: an export that dropped it would not carry it."""
    exported = await use_case([entry(1, 7, date(2026, 9, 21), activity_id=70)]).execute(
        date(2026, 9, 1), date(2026, 9, 30)
    )

    assert exported[0].activity_id == 70
    assert exported[0].activity_label == "Développement"


async def test_off_project_work_carries_no_trade_in_the_export() -> None:
    exported = await use_case([entry(1, 9, date(2026, 9, 21))]).execute(
        date(2026, 9, 1), date(2026, 9, 30)
    )

    assert exported[0].activity_id is None
    assert exported[0].activity_label == ""
