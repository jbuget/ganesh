"""Building a month's entry grid."""

from datetime import date

from src.modules.entries.application.use_cases.get_month_grid import (
    GetMonthGridQuery,
    GetMonthGridUseCase,
)
from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.months.domain.entities.month import Month
from src.modules.projects.domain.entities.activity import Activity
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.enums.work_nature import WorkNature
from tests.helpers.in_memory_repositories import (
    InMemoryActivityRepository,
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
    declared: list[tuple[int, int, int | None, date]] | None = None,
):
    return GetMonthGridUseCase(
        users=InMemoryUserRepository([USER]),
        projects=InMemoryProjectRepository([PORTAIL, ABSENCES]),
        entries=InMemoryEntryRepository(entries or []),
        months=InMemoryMonthRepository(months or []),
        user_missions=InMemoryUserMissionRepository(declared or []),
        activities=InMemoryActivityRepository(),
    )


def entry(project_id: int, day: int, value: float) -> Entry:
    return Entry(
        id=None,
        user_id=1,
        project_id=project_id,
        activity_id=None,
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
            activity_id=None,
            day=date(2026, 8, 3),
            value=DayValue(1.0),
            status_at_entry=ProjectStatus.DEVELOPMENT,
        ),  # un mois anterieur
        Entry(
            id=None,
            user_id=2,
            project_id=10,
            activity_id=None,
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
    grid = await build(declared=[(1, 10, None, date(2026, 9, 1))]).execute(
        GetMonthGridQuery(user_id=1, month=date(2026, 9, 1))
    )

    assert [row.project_id for row in grid.rows] == [10]
    assert grid.rows[0].values == {}
    assert grid.rows[0].total == 0


async def test_a_mission_both_put_on_the_month_and_filled_in_shows_one_row() -> None:
    grid = await build(
        [entry(10, 15, 1.0)], declared=[(1, 10, None, date(2026, 9, 1))]
    ).execute(GetMonthGridQuery(user_id=1, month=date(2026, 9, 1)))

    assert [row.project_id for row in grid.rows] == [10]
    assert grid.rows[0].total == 1.0


async def test_a_mission_put_on_another_month_stays_out_of_the_grid() -> None:
    grid = await build(declared=[(1, 10, None, date(2026, 8, 1))]).execute(
        GetMonthGridQuery(user_id=1, month=date(2026, 9, 1))
    )

    assert grid.rows == []


async def test_a_mission_put_on_a_colleagues_month_stays_out_of_ours() -> None:
    grid = await build(declared=[(2, 10, None, date(2026, 9, 1))]).execute(
        GetMonthGridQuery(user_id=1, month=date(2026, 9, 1))
    )

    assert grid.rows == []


DEV = Activity(
    id=100,
    project_id=10,
    label="Développement",
    nature=WorkNature.DEVELOPMENT,
    estimated_days=15.0,
)
CHEFFERIE = Activity(
    id=101,
    project_id=10,
    label="Chefferie de projet",
    nature=WorkNature.PROJECT_MANAGEMENT,
    estimated_days=5.0,
)


def cut_up_build(
    entries: list[Entry] | None = None,
    declared: list[tuple[int, int, int | None, date]] | None = None,
) -> GetMonthGridUseCase:
    return GetMonthGridUseCase(
        users=InMemoryUserRepository([USER]),
        projects=InMemoryProjectRepository([PORTAIL, ABSENCES]),
        entries=InMemoryEntryRepository(entries or []),
        months=InMemoryMonthRepository([]),
        user_missions=InMemoryUserMissionRepository(declared or []),
        activities=InMemoryActivityRepository([DEV, CHEFFERIE]),
    )


def booked(activity_id: int | None, day: int, value: float) -> Entry:
    return Entry(
        id=None,
        user_id=1,
        project_id=10,
        activity_id=activity_id,
        day=date(2026, 9, day),
        value=DayValue(value),
        status_at_entry=ProjectStatus.DEVELOPMENT,
    )


class TestTheGridReadsByActivity:
    async def test_each_trade_holds_a_line_of_its_own(self) -> None:
        grid = await cut_up_build([booked(100, 15, 1.0), booked(101, 16, 0.5)]).execute(
            GetMonthGridQuery(user_id=1, month=date(2026, 9, 1), today=TODAY)
        )

        assert [(row.project_id, row.activity_id) for row in grid.rows] == [
            (10, 101),
            (10, 100),
        ]

    async def test_a_row_is_named_after_its_activity(self) -> None:
        grid = await cut_up_build([booked(100, 15, 1.0)]).execute(
            GetMonthGridQuery(user_id=1, month=date(2026, 9, 1), today=TODAY)
        )

        assert grid.rows[0].label == "Développement"
        assert grid.rows[0].project_label == "Portail"

    async def test_a_row_reads_the_estimate_of_its_own_trade(self) -> None:
        """Not the mission's: an estimate counted in build days stops meaning
        anything once the days of every trade come off it."""
        grid = await cut_up_build([booked(100, 15, 1.0), booked(101, 16, 0.5)]).execute(
            GetMonthGridQuery(user_id=1, month=date(2026, 9, 1), today=TODAY)
        )

        by_activity = {row.activity_id: row.estimated_days for row in grid.rows}
        assert by_activity == {100: 15.0, 101: 5.0}

    async def test_the_days_consumed_are_counted_per_trade(self) -> None:
        grid = await cut_up_build(
            [booked(100, 15, 1.0), booked(100, 14, 0.5), booked(101, 16, 0.5)]
        ).execute(GetMonthGridQuery(user_id=1, month=date(2026, 9, 1), today=TODAY))

        by_activity = {row.activity_id: row.total_consumed_days for row in grid.rows}
        assert by_activity == {100: 1.5, 101: 0.5}

    async def test_a_day_split_between_two_trades_still_totals_one(self) -> None:
        """The capacity of a day is read across the grid, not down one row."""
        grid = await cut_up_build([booked(100, 15, 0.5), booked(101, 15, 0.5)]).execute(
            GetMonthGridQuery(user_id=1, month=date(2026, 9, 1), today=TODAY)
        )

        fifteenth = next(d for d in grid.day_totals if d.day == date(2026, 9, 15))
        assert fifteenth.total == 1.0
        assert fifteenth.exceeds_capacity is False

    async def test_off_project_work_keeps_a_row_without_an_activity(self) -> None:
        grid = await cut_up_build(
            [
                Entry(
                    id=None,
                    user_id=1,
                    project_id=11,
                    activity_id=None,
                    day=date(2026, 9, 15),
                    value=DayValue(1.0),
                )
            ]
        ).execute(GetMonthGridQuery(user_id=1, month=date(2026, 9, 1), today=TODAY))

        assert [(row.project_id, row.activity_id) for row in grid.rows] == [(11, None)]
        assert grid.rows[0].label == "Absences"

    async def test_a_row_lined_up_without_time_reads_its_activity(self) -> None:
        grid = await cut_up_build(declared=[(1, 10, 101, date(2026, 9, 1))]).execute(
            GetMonthGridQuery(user_id=1, month=date(2026, 9, 1), today=TODAY)
        )

        assert grid.rows[0].label == "Chefferie de projet"
        assert grid.rows[0].values == {}

    async def test_a_row_naming_an_activity_that_no_longer_answers_is_dropped(
        self,
    ) -> None:
        """Drawn under the mission's name it would read as declarable, and
        the write would be refused."""
        grid = await cut_up_build(declared=[(1, 10, 9999, date(2026, 9, 1))]).execute(
            GetMonthGridQuery(user_id=1, month=date(2026, 9, 1), today=TODAY)
        )

        assert grid.rows == []
