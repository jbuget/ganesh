"""Building a month's entry grid."""

from datetime import date

from src.modules.entries.application.use_cases.get_month_grid import (
    GetMonthGridQuery,
    GetMonthGridUseCase,
)
from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.months.domain.entities.month import Month
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryEntryRepository,
    InMemoryMonthRepository,
    InMemoryProjectRepository,
    InMemoryUserMissionRepository,
    InMemoryUserRepository,
)

USER = User(
    id=1,
    entra_oid="oid",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)
PORTAIL = Project(
    id=10,
    label="Portail",
    kind=ProjectKind.PROJECT,
    status=ProjectStatus.DEVELOPMENT,
    estimated_days=20,
)
ABSENCES = Project(id=11, label="Absences", kind=ProjectKind.OFF_PROJECT, status=None)
TODAY = date(2026, 9, 16)


def build(
    entries: list[Entry] | None = None,
    months: list[Month] | None = None,
    declared: list[tuple[int, int, date]] | None = None,
):
    return GetMonthGridUseCase(
        users=InMemoryUserRepository([USER]),
        projects=InMemoryProjectRepository([PORTAIL, ABSENCES]),
        entries=InMemoryEntryRepository(entries or []),
        months=InMemoryMonthRepository(months or []),
        user_missions=InMemoryUserMissionRepository(declared or []),
    )


def entry(project_id: int, day: int, value: float) -> Entry:
    return Entry(
        id=None,
        user_id=1,
        project_id=project_id,
        day=date(2026, 9, day),
        value=DayValue(value),
        status_at_entry=ProjectStatus.DEVELOPMENT,
    )


async def test_the_grid_covers_every_day_of_the_month() -> None:
    grid = await build().execute(GetMonthGridQuery(user_id=1, month=date(2026, 9, 1)))

    assert len(grid.days) == 30


async def test_weekends_and_holidays_are_marked_as_off_days() -> None:
    grid = await build().execute(GetMonthGridQuery(user_id=1, month=date(2026, 9, 1)))
    by_day = {day.day.day: day for day in grid.days}

    assert by_day[12].is_off_day is True  # samedi
    assert by_day[15].is_off_day is False  # mardi


async def test_a_row_is_created_for_each_mission_with_time() -> None:
    grid = await build([entry(10, 15, 1.0)]).execute(
        GetMonthGridQuery(user_id=1, month=date(2026, 9, 1))
    )

    assert [row.project_id for row in grid.rows] == [10]


async def test_each_row_totals_its_time() -> None:
    grid = await build([entry(10, 15, 1.0), entry(10, 16, 0.5)]).execute(
        GetMonthGridQuery(user_id=1, month=date(2026, 9, 1))
    )

    assert grid.rows[0].total == 1.5


async def test_a_row_separates_actual_time_from_forecast() -> None:
    grid = await build([entry(10, 15, 1.0), entry(10, 25, 1.0)]).execute(
        GetMonthGridQuery(user_id=1, month=date(2026, 9, 1), today=TODAY)
    )

    row = grid.rows[0]
    assert row.actual_total == 1.0
    assert row.forecast_total == 1.0
    assert row.total == 2.0


async def test_daily_totals_flag_a_day_above_one() -> None:
    grid = await build([entry(10, 15, 1.0), entry(11, 15, 0.5)]).execute(
        GetMonthGridQuery(user_id=1, month=date(2026, 9, 1))
    )

    overloaded = next(t for t in grid.day_totals if t.day == date(2026, 9, 15))
    assert overloaded.total == 1.5
    assert overloaded.exceeds_capacity is True


async def test_a_normal_day_is_not_flagged() -> None:
    grid = await build([entry(10, 15, 0.5), entry(11, 15, 0.5)]).execute(
        GetMonthGridQuery(user_id=1, month=date(2026, 9, 1))
    )

    day = next(t for t in grid.day_totals if t.day == date(2026, 9, 15))
    assert day.exceeds_capacity is False


async def test_the_grid_reports_the_working_days_of_the_month() -> None:
    grid = await build().execute(GetMonthGridQuery(user_id=1, month=date(2026, 9, 1)))

    assert grid.working_days == 22


async def test_an_untouched_month_is_open_and_editable() -> None:
    grid = await build().execute(GetMonthGridQuery(user_id=1, month=date(2026, 9, 1)))

    assert grid.is_writable is True


async def test_a_validated_month_is_read_only() -> None:
    month = Month(user_id=1, month=date(2026, 9, 1))
    month.validate(by=USER)
    grid = await build(months=[month]).execute(
        GetMonthGridQuery(user_id=1, month=date(2026, 9, 1))
    )

    assert grid.is_writable is False


async def test_a_row_reports_the_whole_project_consumption() -> None:
    """The estimate covers the whole project: so must what is consumed.

    Comparing the month's delivered days to a global estimate would mislead.
    """
    entries = [
        entry(10, 15, 1.0),  # ce mois-ci
        Entry(
            id=None,
            user_id=1,
            project_id=10,
            day=date(2026, 8, 3),
            value=DayValue(1.0),
            status_at_entry=ProjectStatus.DEVELOPMENT,
        ),  # un mois anterieur
        Entry(
            id=None,
            user_id=2,
            project_id=10,
            day=date(2026, 9, 1),
            value=DayValue(0.5),
            status_at_entry=ProjectStatus.DEVELOPMENT,
        ),  # un autre developpeur
    ]
    grid = await build(entries).execute(
        GetMonthGridQuery(user_id=1, month=date(2026, 9, 1), today=TODAY)
    )

    row = grid.rows[0]
    assert row.actual_total == 1.0
    assert row.total_consumed_days == 2.5


async def test_project_consumption_excludes_forecast() -> None:
    """A forecast is not consumed time."""
    grid = await build([entry(10, 15, 1.0), entry(10, 25, 1.0)]).execute(
        GetMonthGridQuery(user_id=1, month=date(2026, 9, 1), today=TODAY)
    )

    assert grid.rows[0].total_consumed_days == 1.0


async def test_the_grid_carries_the_mission_labels() -> None:
    grid = await build([entry(11, 15, 1.0)]).execute(
        GetMonthGridQuery(user_id=1, month=date(2026, 9, 1))
    )

    assert grid.rows[0].label == "Absences"


async def test_a_mission_put_on_the_month_holds_its_row_without_any_time() -> None:
    """Lining up a mission is a gesture of its own: a reload must not undo it."""
    grid = await build(declared=[(1, 10, date(2026, 9, 1))]).execute(
        GetMonthGridQuery(user_id=1, month=date(2026, 9, 1))
    )

    assert [row.project_id for row in grid.rows] == [10]
    assert grid.rows[0].values == {}
    assert grid.rows[0].total == 0


async def test_a_mission_both_put_on_the_month_and_filled_in_shows_one_row() -> None:
    grid = await build(
        [entry(10, 15, 1.0)], declared=[(1, 10, date(2026, 9, 1))]
    ).execute(GetMonthGridQuery(user_id=1, month=date(2026, 9, 1)))

    assert [row.project_id for row in grid.rows] == [10]
    assert grid.rows[0].total == 1.0


async def test_a_mission_put_on_another_month_stays_out_of_the_grid() -> None:
    grid = await build(declared=[(1, 10, date(2026, 8, 1))]).execute(
        GetMonthGridQuery(user_id=1, month=date(2026, 9, 1))
    )

    assert grid.rows == []


async def test_a_mission_put_on_a_colleagues_month_stays_out_of_ours() -> None:
    grid = await build(declared=[(2, 10, date(2026, 9, 1))]).execute(
        GetMonthGridQuery(user_id=1, month=date(2026, 9, 1))
    )

    assert grid.rows == []
