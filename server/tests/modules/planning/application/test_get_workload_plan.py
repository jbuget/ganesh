"""The projection the planning screen reads, and what feeds it."""

from datetime import date

import pytest

from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.planning.application.use_cases.get_workload_plan import (
    GetWorkloadPlanUseCase,
)
from src.modules.planning.domain.entities.workload_plan import PlanBlocker
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectPriority,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.users.domain.entities.user import User
from src.shared.exceptions.domain_exceptions import ValidationError
from tests.helpers.in_memory_repositories import (
    InMemoryEntryRepository,
    InMemoryProjectAssigneeRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
)

# A Friday. The window therefore opens on a working day.
TODAY = date(2026, 9, 18)

ALICE = User(id=1, entra_oid="a", email="alice@waat.fr", display_name="Alice")
BOB = User(id=2, entra_oid="b", email="bob@waat.fr", display_name="Bob")


def a_mission(
    project_id: int = 10,
    label: str = "Portail",
    status: ProjectStatus = ProjectStatus.DEVELOPMENT,
    estimated: float | None = 5.0,
    priority: ProjectPriority | None = ProjectPriority.NORMAL,
    kind: ProjectKind = ProjectKind.PROJECT,
    is_active: bool = True,
    go_live: date | None = None,
    parent_id: int | None = None,
) -> Project:
    return Project(
        id=project_id,
        label=label,
        kind=kind,
        status=status,
        estimated_days=estimated,
        priority=priority,
        is_active=is_active,
        go_live_date=go_live,
        parent_id=parent_id,
    )


def entries_on(
    project_id: int, days: list[date], user_id: int = 1, value: float = 1.0
) -> list[Entry]:
    return [
        Entry(
            id=None,
            user_id=user_id,
            project_id=project_id,
            activity_id=None,
            day=day,
            value=DayValue(value),
            status_at_entry=ProjectStatus.DEVELOPMENT,
        )
        for day in days
    ]


def a_use_case(
    missions: list[Project],
    entries: list[Entry] | None = None,
    contributors: dict[int, list[int]] | None = None,
    leads: dict[int, list[int]] | None = None,
    users: list[User] | None = None,
) -> GetWorkloadPlanUseCase:
    assignments: dict[tuple[int, ProjectRole], list[int]] = {}
    for project_id, user_ids in (contributors or {}).items():
        assignments[(project_id, ProjectRole.CONTRIBUTOR)] = list(user_ids)
    for project_id, user_ids in (leads or {}).items():
        assignments[(project_id, ProjectRole.LEAD)] = list(user_ids)

    return GetWorkloadPlanUseCase(
        projects=InMemoryProjectRepository(missions),
        entries=InMemoryEntryRepository(entries or []),
        assignees=InMemoryProjectAssigneeRepository(assignments),
        users=InMemoryUserRepository(users if users is not None else [ALICE, BOB]),
    )


def row(reading, project_id: int):
    return next(r for r in reading.missions if r.mission.id == project_id)


class TestWhatTheBacklogHolds:
    @pytest.mark.asyncio
    async def test_a_mission_in_operations_is_not_planned_any_more(self) -> None:
        """The plan steers what is being built, not what is being kept alive."""
        reading = await a_use_case(
            [a_mission(10, status=ProjectStatus.OPERATIONS)],
            contributors={10: [1]},
        ).execute(today=TODAY)

        assert reading.missions == []

    @pytest.mark.asyncio
    async def test_an_off_project_activity_never_enters_the_plan(self) -> None:
        reading = await a_use_case(
            [a_mission(10, kind=ProjectKind.OFF_PROJECT, status=None)],
            contributors={10: [1]},
        ).execute(today=TODAY)

        assert reading.missions == []

    @pytest.mark.asyncio
    async def test_an_archived_mission_never_enters_the_plan(self) -> None:
        reading = await a_use_case(
            [a_mission(10, is_active=False)], contributors={10: [1]}
        ).execute(today=TODAY)

        assert reading.missions == []

    @pytest.mark.asyncio
    async def test_a_work_package_is_planned_on_its_own(self) -> None:
        """It carries its own estimate and its own people: rolling it into its
        parent would count the same days twice."""
        reading = await a_use_case(
            [
                a_mission(10, status=ProjectStatus.OPERATIONS),
                a_mission(11, kind=ProjectKind.WORK_PACKAGE, parent_id=10),
            ],
            contributors={11: [1]},
        ).execute(today=TODAY)

        assert [r.mission.id for r in reading.missions] == [11]


class TestWhatIsLeftToDo:
    @pytest.mark.asyncio
    async def test_days_already_delivered_come_off_the_estimate(self) -> None:
        reading = await a_use_case(
            [a_mission(10, estimated=5.0)],
            entries=entries_on(10, [date(2026, 9, 16), date(2026, 9, 17)]),
            contributors={10: [1]},
        ).execute(today=TODAY)

        assert row(reading, 10).projected.remaining_days == 3.0

    @pytest.mark.asyncio
    async def test_days_already_forecast_come_off_the_estimate_too(self) -> None:
        """A forecast entered by hand is a piece of the plan already made:
        planning it again would book the same days twice."""
        reading = await a_use_case(
            [a_mission(10, estimated=5.0)],
            entries=entries_on(10, [date(2026, 9, 21), date(2026, 9, 22)]),
            contributors={10: [1]},
        ).execute(today=TODAY)

        assert row(reading, 10).projected.remaining_days == 3.0

    @pytest.mark.asyncio
    async def test_an_estimate_already_overrun_leaves_nothing_to_place(self) -> None:
        reading = await a_use_case(
            [a_mission(10, estimated=1.0)],
            entries=entries_on(10, [date(2026, 9, 16), date(2026, 9, 17)]),
            contributors={10: [1]},
        ).execute(today=TODAY)

        landed = row(reading, 10).projected
        assert (landed.remaining_days, landed.blocker) == (
            0.0,
            PlanBlocker.NOTHING_LEFT,
        )

    @pytest.mark.asyncio
    async def test_a_mission_nobody_estimated_is_reported(self) -> None:
        reading = await a_use_case(
            [a_mission(10, estimated=None)], contributors={10: [1]}
        ).execute(today=TODAY)

        assert row(reading, 10).projected.blocker is PlanBlocker.NO_ESTIMATE


class TestWhoCarriesTheWork:
    @pytest.mark.asyncio
    async def test_contributors_are_the_people_the_work_is_placed_on(self) -> None:
        reading = await a_use_case(
            [a_mission(10, estimated=4.0)], contributors={10: [1, 2]}
        ).execute(today=TODAY)

        assert [u.id for u in row(reading, 10).assignees] == [1, 2]

    @pytest.mark.asyncio
    async def test_a_lead_who_does_not_contribute_carries_no_build(self) -> None:
        """A lead answers for the choices; they do not thereby take the days.
        A mission with a lead and no contributor is one to staff, and saying so
        is more useful than lending it a pair of hands it has not got."""
        reading = await a_use_case(
            [a_mission(10, estimated=4.0)], leads={10: [1]}
        ).execute(today=TODAY)

        assert row(reading, 10).projected.blocker is PlanBlocker.NO_ASSIGNEE

    @pytest.mark.asyncio
    async def test_everyone_active_appears_in_the_diaries_read(self) -> None:
        """Knowing who is free matters as much as knowing who is taken."""
        reading = await a_use_case(
            [a_mission(10, estimated=4.0)], contributors={10: [1]}
        ).execute(today=TODAY)

        assert [p.user.id for p in reading.people] == [1, 2]


class TestLandingAndSlippage:
    @pytest.mark.asyncio
    async def test_the_projection_lands_the_mission_on_a_working_day(self) -> None:
        """Five days from Friday 18 September land on Friday 25: the half day
        held back each week pushes what a bare count would put on Thursday."""
        reading = await a_use_case(
            [a_mission(10, estimated=5.0)], contributors={10: [1]}
        ).execute(today=TODAY)

        assert row(reading, 10).projected.ends_on == date(2026, 9, 25)

    @pytest.mark.asyncio
    async def test_landing_after_the_date_announced_reads_as_late(self) -> None:
        reading = await a_use_case(
            [a_mission(10, estimated=5.0, go_live=date(2026, 9, 21))],
            contributors={10: [1]},
        ).execute(today=TODAY)

        assert row(reading, 10).slippage_days == 4

    @pytest.mark.asyncio
    async def test_landing_ahead_of_the_date_announced_reads_as_early(self) -> None:
        reading = await a_use_case(
            [a_mission(10, estimated=5.0, go_live=date(2026, 10, 1))],
            contributors={10: [1]},
        ).execute(today=TODAY)

        assert row(reading, 10).slippage_days == -6

    @pytest.mark.asyncio
    async def test_a_mission_with_no_announced_date_is_never_late(self) -> None:
        reading = await a_use_case(
            [a_mission(10, estimated=5.0)], contributors={10: [1]}
        ).execute(today=TODAY)

        assert row(reading, 10).slippage_days is None


class TestTheWhatIf:
    @pytest.mark.asyncio
    async def test_without_a_hypothesis_urgency_decides_the_order(self) -> None:
        reading = await a_use_case(
            [
                a_mission(10, estimated=2.0, priority=ProjectPriority.LOW),
                a_mission(20, estimated=2.0, priority=ProjectPriority.CRITICAL),
            ],
            contributors={10: [1], 20: [1]},
        ).execute(today=TODAY)

        assert [r.mission.id for r in reading.missions] == [20, 10]
        assert row(reading, 20).projected.ends_on == date(2026, 9, 22)

    @pytest.mark.asyncio
    async def test_the_hypothesis_reorders_the_backlog_and_moves_the_dates(
        self,
    ) -> None:
        """The heart of the screen: ask what happens if this one goes first,
        and read who lands later for it."""
        reading = await a_use_case(
            [
                a_mission(10, estimated=2.0, priority=ProjectPriority.LOW),
                a_mission(20, estimated=2.0, priority=ProjectPriority.CRITICAL),
            ],
            contributors={10: [1], 20: [1]},
        ).execute(today=TODAY, order=[10, 20])

        assert [r.mission.id for r in reading.missions] == [10, 20]
        assert row(reading, 10).projected.ends_on == date(2026, 9, 22)
        assert row(reading, 20).projected.ends_on == date(2026, 9, 24)

    @pytest.mark.asyncio
    async def test_a_hypothesis_writes_nothing_down(self) -> None:
        """Arbitrating must cost nothing: the board is only changed on purpose,
        never by looking at a projection."""
        missions = [
            a_mission(10, estimated=2.0, priority=ProjectPriority.LOW),
            a_mission(20, estimated=2.0, priority=ProjectPriority.CRITICAL),
        ]
        use_case = a_use_case(missions, contributors={10: [1], 20: [1]})

        await use_case.execute(today=TODAY, order=[10, 20])
        after = await use_case.execute(today=TODAY)

        assert [r.mission.id for r in after.missions] == [20, 10]


class TestHorizon:
    @pytest.mark.asyncio
    async def test_the_window_runs_from_today_to_the_end_of_the_horizon(self) -> None:
        reading = await a_use_case([], users=[ALICE]).execute(
            today=TODAY, horizon_months=1
        )

        assert (reading.from_day, reading.to_day) == (TODAY, date(2026, 10, 17))

    @pytest.mark.asyncio
    async def test_what_does_not_fit_the_horizon_says_so(self) -> None:
        reading = await a_use_case(
            [a_mission(10, estimated=200.0)], contributors={10: [1]}
        ).execute(today=TODAY, horizon_months=1)

        assert row(reading, 10).projected.blocker is PlanBlocker.BEYOND_HORIZON

    @pytest.mark.asyncio
    async def test_an_impossible_horizon_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            await a_use_case([]).execute(today=TODAY, horizon_months=0)


class TestStaffingHypothesis:
    @pytest.mark.asyncio
    async def test_putting_someone_on_a_mission_brings_its_landing_forward(
        self,
    ) -> None:
        """The strongest lever of an arbitration: a second pair of hands."""
        missions = [a_mission(10, estimated=4.0)]
        alone = await a_use_case(missions, contributors={10: [1]}).execute(today=TODAY)
        paired = await a_use_case(missions, contributors={10: [1]}).execute(
            today=TODAY, staffing={10: [1, 2]}
        )

        assert row(alone, 10).projected.ends_on == date(2026, 9, 24)
        assert row(paired, 10).projected.ends_on == date(2026, 9, 22)

    @pytest.mark.asyncio
    async def test_taking_everyone_off_a_mission_leaves_it_unplannable(self) -> None:
        reading = await a_use_case(
            [a_mission(10, estimated=4.0)], contributors={10: [1]}
        ).execute(today=TODAY, staffing={10: []})

        assert row(reading, 10).projected.blocker is PlanBlocker.NO_ASSIGNEE

    @pytest.mark.asyncio
    async def test_a_mission_the_hypothesis_leaves_alone_keeps_its_own_team(
        self,
    ) -> None:
        reading = await a_use_case(
            [a_mission(10, estimated=4.0), a_mission(20, estimated=4.0)],
            contributors={10: [1], 20: [2]},
        ).execute(today=TODAY, staffing={10: [1, 2]})

        assert [u.id for u in row(reading, 20).assignees] == [2]

    @pytest.mark.asyncio
    async def test_the_hypothesis_shows_in_who_the_row_names(self) -> None:
        """What the screen draws must be what the projection used."""
        reading = await a_use_case(
            [a_mission(10, estimated=4.0)], contributors={10: [1]}
        ).execute(today=TODAY, staffing={10: [1, 2]})

        assert [u.id for u in row(reading, 10).assignees] == [1, 2]

    @pytest.mark.asyncio
    async def test_a_hypothesis_on_staffing_writes_nothing_down(self) -> None:
        use_case = a_use_case([a_mission(10, estimated=4.0)], contributors={10: [1]})

        await use_case.execute(today=TODAY, staffing={10: [1, 2]})
        after = await use_case.execute(today=TODAY)

        assert [u.id for u in row(after, 10).assignees] == [1]


class TestSummary:
    @pytest.mark.asyncio
    async def test_it_counts_what_lands_and_what_is_late(self) -> None:
        reading = await a_use_case(
            [
                a_mission(10, estimated=2.0, go_live=date(2026, 9, 1)),
                a_mission(20, estimated=2.0, go_live=date(2026, 12, 1)),
            ],
            contributors={10: [1], 20: [1]},
        ).execute(today=TODAY)

        assert (reading.summary.planned, reading.summary.late) == (2, 1)

    @pytest.mark.asyncio
    async def test_it_calls_out_the_missions_nobody_is_on(self) -> None:
        reading = await a_use_case(
            [a_mission(10, estimated=2.0), a_mission(20, estimated=None)]
        ).execute(today=TODAY)

        assert (reading.summary.blocked, reading.summary.unassigned) == (2, 1)

    @pytest.mark.asyncio
    async def test_it_totals_the_capacity_nobody_took(self) -> None:
        """Twenty-one working days, less the half day held back on each of the
        five weeks they span."""
        reading = await a_use_case([], users=[ALICE]).execute(
            today=TODAY, horizon_months=1
        )

        assert reading.summary.free_days == 18.5
