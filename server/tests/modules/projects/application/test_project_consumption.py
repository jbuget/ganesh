"""What a project has cost, trade by trade, lots included."""

from datetime import date

import pytest

from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.projects.application.use_cases.get_project_consumption import (
    GetProjectConsumptionUseCase,
)
from src.modules.projects.domain.entities.activity import Activity
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from tests.helpers.in_memory_repositories import (
    InMemoryActivityRepository,
    InMemoryEntryRepository,
    InMemoryProjectRepository,
)

TODAY = date(2026, 9, 21)

NOMAD = Project(
    id=1, label="Nomad", kind=ProjectKind.PROJECT, status=ProjectStatus.DEVELOPMENT
)
IMPORT = Project(
    id=2,
    label="Nomad — Import",
    kind=ProjectKind.WORK_PACKAGE,
    status=ProjectStatus.SCOPING,
    parent_id=1,
)
DEV = Activity(id=10, project_id=1, label="Développement", estimated_days=20)
LOT_DEV = Activity(id=20, project_id=2, label="Développement", estimated_days=4)


def entry(project_id: int, activity_id: int | None, day: date, value: float) -> Entry:
    return Entry(
        id=None,
        user_id=1,
        project_id=project_id,
        activity_id=activity_id,
        day=day,
        value=DayValue(value),
        status_at_entry=ProjectStatus.DEVELOPMENT,
    )


def booked(
    project_id: int, activity_id: int | None, first: date, days: int
) -> list[Entry]:
    """`days` whole days in a row from `first` — an entry holds one day at most."""
    return [
        entry(project_id, activity_id, first.replace(day=first.day + rank), 1.0)
        for rank in range(days)
    ]


def build(
    entries: list[Entry] | None = None,
    activities: list[Activity] | None = None,
    projects: list[Project] | None = None,
) -> GetProjectConsumptionUseCase:
    return GetProjectConsumptionUseCase(
        projects=InMemoryProjectRepository(projects or [NOMAD, IMPORT]),
        activities=InMemoryActivityRepository(activities or [DEV, LOT_DEV]),
        entries=InMemoryEntryRepository(entries or []),
    )


@pytest.mark.asyncio
async def test_the_trades_of_the_project_are_read_with_what_each_has_left() -> None:
    sheet = await build(booked(1, 10, date(2026, 9, 1), 5)).execute(1, TODAY)

    assert sheet.project is NOMAD
    [dev] = sheet.trades
    assert dev.activity is DEV
    assert dev.delivered == 5.0
    assert dev.left == 15.0


@pytest.mark.asyncio
async def test_each_work_package_is_read_on_its_own_trades() -> None:
    sheet = await build(
        [*booked(1, 10, date(2026, 9, 1), 5), entry(2, 20, date(2026, 9, 2), 1.0)]
    ).execute(1, TODAY)

    [lot] = sheet.work_packages
    assert lot.project is IMPORT
    assert [t.delivered for t in lot.trades] == [1.0]
    assert [t.delivered for t in sheet.trades] == [5.0]


@pytest.mark.asyncio
async def test_a_work_package_is_read_for_itself_with_no_lots_under_it() -> None:
    sheet = await build([entry(2, 20, date(2026, 9, 2), 1.0)]).execute(2, TODAY)

    assert sheet.project is IMPORT
    assert sheet.work_packages == []
    assert [t.delivered for t in sheet.trades] == [1.0]


@pytest.mark.asyncio
async def test_forecast_is_kept_apart_from_what_was_delivered() -> None:
    sheet = await build(booked(1, 10, date(2026, 9, 28), 2)).execute(1, TODAY)

    assert sheet.trades[0].delivered == 0
    assert sheet.trades[0].forecast == 2.0


@pytest.mark.asyncio
async def test_a_project_nobody_can_find_is_refused() -> None:
    with pytest.raises(EntityNotFoundError):
        await build().execute(404, TODAY)
