"""What the reference list tells of the cost of a mission.

An estimate covers the build. A mission that runs consumes on top of it, and
the two readings must not be confused: a ratio while it is built, a pace once
it lives.
"""

from dataclasses import replace
from datetime import date, timedelta

from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.projects.application.use_cases.list_projects import ListProjectsUseCase
from src.modules.projects.domain.entities.activity import Activity
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.shared.enums.work_nature import WorkNature
from tests.helpers.in_memory_repositories import (
    InMemoryActivityRepository,
    InMemoryEntryRepository,
    InMemoryProjectAssigneeRepository,
    InMemoryProjectDetailRepository,
    InMemoryProjectRepository,
    InMemoryProjectUpdateRepository,
    InMemoryUserRepository,
)

TODAY = date(2026, 9, 18)

PORTAIL = Project(
    id=10,
    label="Portail",
    kind=ProjectKind.PROJECT,
    status=ProjectStatus.OPERATIONS,
    estimated_days=20.0,
)
REFONTE = Project(
    id=11,
    label="Refonte recherche",
    kind=ProjectKind.WORK_PACKAGE,
    parent_id=10,
    status=ProjectStatus.DEVELOPMENT,
    estimated_days=6.0,
)


def days_spent(
    project_id: int,
    ending: date,
    status: ProjectStatus | None,
    count: int = 1,
) -> list[Entry]:
    """`count` full days declared on a mission, ending on `ending`.

    A single entry is worth half a day or a day, never more: twenty days of
    build are twenty entries, which is also what the screen counts.
    """
    return [
        Entry(
            id=None,
            user_id=1,
            project_id=project_id,
            activity_id=None,
            day=ending - timedelta(days=offset),
            value=DayValue(1.0),
            status_at_entry=status,
        )
        for offset in range(count)
    ]


async def listed(
    entries: list[Entry],
    missions: list[Project] | None = None,
    live_since: dict[int, date] | None = None,
    activities: list[Activity] | None = None,
):
    details = InMemoryProjectDetailRepository()
    for project_id, day in (live_since or {}).items():
        await details.mark_phase_reached(project_id, ProjectStatus.OPERATIONS, day)

    use_case = ListProjectsUseCase(
        projects=InMemoryProjectRepository(missions or [PORTAIL]),
        activities=InMemoryActivityRepository(activities or []),
        entries=InMemoryEntryRepository(entries),
        assignees=InMemoryProjectAssigneeRepository({}),
        users=InMemoryUserRepository([]),
        updates=InMemoryProjectUpdateRepository(),
        details=details,
    )
    missions_listees = await use_case.execute(today=TODAY)
    return {m.project.id: m for m in missions_listees}


async def test_days_spent_before_operations_count_as_build() -> None:
    par_id = await listed(
        days_spent(10, TODAY - timedelta(days=200), ProjectStatus.SCOPING, 2)
        + days_spent(10, TODAY - timedelta(days=150), ProjectStatus.DEVELOPMENT, 1)
    )

    assert par_id[10].cost.build_days == 3.0
    assert par_id[10].cost.run_days == 0.0


async def test_days_spent_in_operations_count_as_run() -> None:
    par_id = await listed(
        days_spent(10, TODAY - timedelta(days=200), ProjectStatus.DEVELOPMENT, 20)
        + days_spent(10, TODAY - timedelta(days=10), ProjectStatus.OPERATIONS, 1)
    )

    assert (par_id[10].cost.build_days, par_id[10].cost.run_days) == (20.0, 1.0)


async def test_run_never_makes_a_mission_overrun_its_build_estimate() -> None:
    """Portail was estimated at twenty days and has been kept alive for forty.
    It is not late: the estimate never covered its operations."""
    par_id = await listed(
        days_spent(10, TODAY - timedelta(days=300), ProjectStatus.DEVELOPMENT, 18)
        + days_spent(10, TODAY - timedelta(days=150), ProjectStatus.OPERATIONS, 40)
    )

    assert par_id[10].cost.has_overrun is False


async def test_a_build_past_its_estimate_is_reported() -> None:
    par_id = await listed(
        days_spent(10, TODAY - timedelta(days=300), ProjectStatus.DEVELOPMENT, 24)
    )

    assert par_id[10].cost.has_overrun is True


async def test_the_pace_is_read_over_the_recent_window_only() -> None:
    """Forty days spent two years ago say nothing of what the service costs
    today: only the last quarter feeds the pace."""
    par_id = await listed(
        days_spent(10, TODAY - timedelta(days=400), ProjectStatus.OPERATIONS, 40)
        + days_spent(10, TODAY - timedelta(days=30), ProjectStatus.OPERATIONS, 6),
        live_since={10: TODAY - timedelta(days=400)},
    )

    assert par_id[10].cost.run_days == 46.0
    assert par_id[10].cost.monthly_run_rate(TODAY) == 2.0


async def test_a_mission_that_has_just_gone_live_announces_no_pace() -> None:
    par_id = await listed(
        days_spent(10, TODAY - timedelta(days=5), ProjectStatus.OPERATIONS, 2),
        live_since={10: TODAY - timedelta(days=10)},
    )

    assert par_id[10].cost.monthly_run_rate(TODAY) is None


async def test_a_parent_carries_what_its_work_packages_cost() -> None:
    par_id = await listed(
        days_spent(10, TODAY - timedelta(days=300), ProjectStatus.DEVELOPMENT, 20)
        + days_spent(10, TODAY - timedelta(days=100), ProjectStatus.OPERATIONS, 30)
        + days_spent(11, TODAY - timedelta(days=20), ProjectStatus.DEVELOPMENT, 4),
        missions=[PORTAIL, REFONTE],
        live_since={10: TODAY - timedelta(days=200)},
    )

    assert par_id[10].tree_cost.build_days == 24.0
    assert par_id[10].tree_cost.run_days == 30.0
    assert par_id[10].tree_cost.estimated_days == 26.0


async def test_a_work_package_keeps_reading_its_own_cost() -> None:
    """Unfolded, every row speaks of itself: the totals belong to the parent."""
    par_id = await listed(
        days_spent(10, TODAY - timedelta(days=300), ProjectStatus.DEVELOPMENT, 20)
        + days_spent(11, TODAY - timedelta(days=20), ProjectStatus.DEVELOPMENT, 4),
        missions=[PORTAIL, REFONTE],
    )

    assert par_id[11].cost.build_days == 4.0
    assert par_id[11].tree_cost.build_days == 4.0


async def test_an_entry_without_a_phase_counts_as_build() -> None:
    par_id = await listed(days_spent(10, TODAY - timedelta(days=5), None, 2))

    assert (par_id[10].cost.build_days, par_id[10].cost.run_days) == (2.0, 0.0)


async def test_a_forecast_is_not_a_cost() -> None:
    """A day declared ahead has not been spent, whatever phase it falls in."""
    par_id = await listed(
        days_spent(10, TODAY + timedelta(days=3), ProjectStatus.OPERATIONS, 1)
    )

    assert par_id[10].cost.run_days == 0.0


def a_trade(
    estimated_days: float | None, label: str = "Développement", project_id: int = 10
) -> Activity:
    return Activity(
        id=None,
        project_id=project_id,
        label=label,
        nature=WorkNature.DEVELOPMENT,
        estimated_days=estimated_days,
    )


class TestTheEstimateIsReadFromTheTrades:
    """After the reprise a mission holds no estimate of its own: the budget
    lives on its activities, and the mission reads their sum."""

    async def test_a_mission_reads_the_sum_of_what_its_trades_are_budgeted_at(
        self,
    ) -> None:
        par_id = await listed(
            [],
            missions=[replace(PORTAIL, estimated_days=None)],
            activities=[a_trade(15.0), a_trade(5.0, label="Chefferie de projet")],
        )

        assert par_id[10].cost.estimated_days == 20.0

    async def test_one_trade_left_unbudgeted_leaves_the_mission_unestimated(
        self,
    ) -> None:
        """A ratio drawn from half a budget turns red on a screen people steer
        by, and announces an overrun nobody measured."""
        par_id = await listed(
            [],
            missions=[replace(PORTAIL, estimated_days=None)],
            activities=[a_trade(15.0), a_trade(None, label="Chefferie de projet")],
        )

        assert par_id[10].cost.estimated_days is None
        assert par_id[10].cost.has_overrun is False

    async def test_a_mission_nobody_cut_up_still_reads_its_own_estimate(self) -> None:
        par_id = await listed([], missions=[PORTAIL])

        assert par_id[10].cost.estimated_days == PORTAIL.estimated_days
