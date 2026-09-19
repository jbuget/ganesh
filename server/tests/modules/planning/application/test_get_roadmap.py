"""The roadmap the screen reads: what is delivered, what is promised, when."""

from datetime import date

import pytest

from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.planning.application.use_cases.get_roadmap import GetRoadmapUseCase
from src.modules.planning.domain.entities.roadmap import SegmentKind
from src.modules.planning.domain.entities.workload_plan import PlanBlocker
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.users.domain.entities.user import User
from src.shared.exceptions.domain_exceptions import ValidationError
from tests.helpers.in_memory_repositories import (
    InMemoryEntryRepository,
    InMemoryProjectAssigneeRepository,
    InMemoryProjectDetailRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
)

# A Friday, so the window opens on a working day.
TODAY = date(2026, 9, 18)
FROM_DAY = date(2026, 1, 1)
TO_DAY = date(2026, 12, 31)

ALICE = User(id=1, entra_oid="a", email="alice@waat.fr", display_name="Alice")


def a_mission(
    project_id: int = 10,
    label: str = "Portail",
    status: ProjectStatus | None = ProjectStatus.DEVELOPMENT,
    kind: ProjectKind = ProjectKind.PROJECT,
    estimated: float | None = 5.0,
    go_live: date | None = None,
    category: ProjectCategory | None = None,
    is_active: bool = True,
    parent_id: int | None = None,
) -> Project:
    return Project(
        id=project_id,
        label=label,
        kind=kind,
        status=status,
        estimated_days=estimated,
        go_live_date=go_live,
        category=category,
        is_active=is_active,
        parent_id=parent_id,
    )


def entries_on(project_id: int, days: list[date]) -> list[Entry]:
    return [
        Entry(
            id=None,
            user_id=1,
            project_id=project_id,
            day=day,
            value=DayValue(1.0),
            status_at_entry=ProjectStatus.DEVELOPMENT,
        )
        for day in days
    ]


async def read(
    missions: list[Project],
    entries: list[Entry] | None = None,
    phases: dict[int, dict[ProjectStatus, date]] | None = None,
    assigned: bool = True,
    from_day: date | None = FROM_DAY,
    to_day: date | None = TO_DAY,
):
    details = InMemoryProjectDetailRepository()
    for project_id, crossings in (phases or {}).items():
        for status, day in crossings.items():
            await details.mark_phase_reached(project_id, status, day)

    assignees = InMemoryProjectAssigneeRepository()
    if assigned:
        for mission in missions:
            assert mission.id is not None
            await assignees.assign(mission.id, 1, ProjectRole.CONTRIBUTOR)

    use_case = GetRoadmapUseCase(
        projects=InMemoryProjectRepository(missions),
        entries=InMemoryEntryRepository(entries or []),
        details=details,
        assignees=assignees,
        users=InMemoryUserRepository([ALICE]),
    )
    return await use_case.execute(from_day=from_day, to_day=to_day, today=TODAY)


class TestWhatTheRoadmapShows:
    async def test_a_mission_under_way_carries_what_it_lived_and_what_is_supposed(
        self,
    ) -> None:
        roadmap = await read(
            [a_mission()],
            entries=entries_on(10, [date(2026, 5, 4)]),
            phases={10: {ProjectStatus.DEVELOPMENT: date(2026, 5, 4)}},
        )

        [line] = roadmap.missions
        assert [segment.kind for segment in line.segments] == [
            SegmentKind.LIVED,
            SegmentKind.PROJECTED,
        ]
        assert line.landing_date is not None

    async def test_off_project_work_never_appears(self) -> None:
        roadmap = await read(
            [
                a_mission(),
                a_mission(11, "Congés", status=None, kind=ProjectKind.OFF_PROJECT),
            ]
        )

        assert [line.project_id for line in roadmap.missions] == [10]

    async def test_a_mission_with_nothing_inside_the_window_is_left_out(self) -> None:
        # Delivered two years ago, archived since: it has nothing to say here.
        roadmap = await read(
            [a_mission(status=ProjectStatus.OPERATIONS, is_active=False)],
            entries=entries_on(10, [date(2024, 3, 2)]),
            phases={10: {ProjectStatus.OPERATIONS: date(2024, 4, 1)}},
        )

        assert roadmap.missions == []

    async def test_a_mission_never_estimated_still_shows_on_the_date_it_promised(
        self,
    ) -> None:
        roadmap = await read([a_mission(estimated=None, go_live=date(2026, 11, 30))])

        [line] = roadmap.missions
        assert line.segments == []
        assert line.target_date == date(2026, 11, 30)

    async def test_a_work_package_answers_with_the_axis_of_its_project(self) -> None:
        roadmap = await read(
            [
                a_mission(10, "Portail", category=ProjectCategory.INNOVATE),
                a_mission(
                    11,
                    "Export",
                    kind=ProjectKind.WORK_PACKAGE,
                    parent_id=10,
                    go_live=date(2026, 10, 1),
                ),
            ]
        )

        axes = {line.project_id: line.category for line in roadmap.missions}
        assert axes[11] is ProjectCategory.INNOVATE


class TestWhatItPromised:
    async def test_a_landing_past_the_date_announced_is_called_late(self) -> None:
        # Thirty days of build for one person, at four and a half a week: it
        # lands in November, and October was announced.
        roadmap = await read([a_mission(estimated=30.0, go_live=date(2026, 10, 1))])

        [line] = roadmap.missions
        assert line.is_late
        assert line.slippage_days is not None and line.slippage_days > 0

    async def test_a_mission_with_no_date_announced_is_never_late(self) -> None:
        roadmap = await read([a_mission(estimated=30.0)])

        [line] = roadmap.missions
        assert not line.is_late
        assert line.slippage_days is None


class TestWhatIsInTheWay:
    async def test_a_mission_nobody_is_on_says_so_rather_than_drawing_nothing(
        self,
    ) -> None:
        roadmap = await read([a_mission()], assigned=False)

        [line] = roadmap.missions
        assert line.blocker is PlanBlocker.NO_ASSIGNEE
        assert line.segments == []

    async def test_a_mission_nobody_estimated_says_so(self) -> None:
        roadmap = await read([a_mission(estimated=None)])

        [line] = roadmap.missions
        assert line.blocker is PlanBlocker.NO_ESTIMATE

    async def test_a_mission_that_does_not_fit_the_window_says_so(self) -> None:
        # Eighty days for one person cannot land before the year is out.
        roadmap = await read([a_mission(estimated=80.0)])

        [line] = roadmap.missions
        assert line.blocker is PlanBlocker.BEYOND_HORIZON
        assert line.landing_date is None


class TestHowItReads:
    async def test_lines_run_chronologically_so_the_eye_sweeps_the_diagonal(
        self,
    ) -> None:
        roadmap = await read(
            [
                a_mission(10, "Commencée en juin"),
                a_mission(11, "Commencée en mars"),
            ],
            entries=entries_on(10, [date(2026, 6, 1)])
            + entries_on(11, [date(2026, 3, 2)]),
            phases={
                10: {ProjectStatus.DEVELOPMENT: date(2026, 6, 1)},
                11: {ProjectStatus.DEVELOPMENT: date(2026, 3, 2)},
            },
        )

        assert [line.label for line in roadmap.missions] == [
            "Commencée en mars",
            "Commencée en juin",
        ]

    async def test_a_mission_with_no_bar_and_no_date_reads_last(self) -> None:
        roadmap = await read(
            [
                a_mission(10, "Sans rien", estimated=None),
                a_mission(
                    11, "Promise en octobre", estimated=None, go_live=date(2026, 10, 1)
                ),
            ]
        )

        assert [line.label for line in roadmap.missions] == [
            "Promise en octobre",
            "Sans rien",
        ]


class TestTheTallyAbove:
    async def test_it_counts_the_lines_drawn(self) -> None:
        roadmap = await read([a_mission(10), a_mission(11, "Socle")])

        assert roadmap.summary.missions == 2

    async def test_it_names_what_is_missing_before_the_drawing_can_be_believed(
        self,
    ) -> None:
        roadmap = await read(
            [
                a_mission(10, "Sans estimation", estimated=None),
                a_mission(11, "Sans date", go_live=None),
            ]
        )

        assert roadmap.summary.unestimated == 1
        assert roadmap.summary.undated == 2

    async def test_a_service_that_went_live_in_the_window_counts_as_delivered(
        self,
    ) -> None:
        roadmap = await read(
            [a_mission(status=ProjectStatus.OPERATIONS)],
            entries=entries_on(10, [date(2026, 3, 2)]),
            phases={10: {ProjectStatus.OPERATIONS: date(2026, 4, 1)}},
        )

        assert roadmap.summary.delivered == 1

    async def test_a_service_nobody_dated_the_go_live_of_is_not_a_delivery(
        self,
    ) -> None:
        # Twenty-three services were on the reference list before anybody
        # started recording phases. Their rule has to open somewhere, and
        # where it opens must never be counted as a mise en service — or the
        # bandeau announces a month of deliveries that never happened.
        roadmap = await read(
            [
                a_mission(10, status=ProjectStatus.OPERATIONS),
                a_mission(11, "Autre", status=ProjectStatus.OPERATIONS),
            ]
        )

        assert roadmap.summary.delivered == 0
        assert all(line.went_live_on is None for line in roadmap.missions)

    async def test_a_service_nobody_dated_opens_its_rule_at_the_window(self) -> None:
        roadmap = await read([a_mission(status=ProjectStatus.OPERATIONS)])

        assert [
            (s.kind, s.starts_on, s.ends_on) for s in roadmap.missions[0].segments
        ] == [(SegmentKind.RUNNING, FROM_DAY, TO_DAY)]


class TestWhatItSaysAboutADateAnnounced:
    async def test_a_service_that_went_live_late_carries_a_settled_slip(self) -> None:
        roadmap = await read(
            [a_mission(status=ProjectStatus.OPERATIONS, go_live=date(2026, 4, 1))],
            phases={10: {ProjectStatus.OPERATIONS: date(2026, 6, 15)}},
        )

        line = roadmap.missions[0]
        assert (line.went_live_on, line.slippage_days, line.is_late) == (
            date(2026, 6, 15),
            75,
            True,
        )
        assert roadmap.summary.late == 1

    async def test_a_service_that_went_live_on_time_is_not_late(self) -> None:
        roadmap = await read(
            [a_mission(status=ProjectStatus.OPERATIONS, go_live=date(2026, 6, 15))],
            phases={10: {ProjectStatus.OPERATIONS: date(2026, 6, 15)}},
        )

        assert (roadmap.missions[0].slippage_days, roadmap.summary.late) == (0, 0)

    async def test_a_service_live_but_undated_owes_no_slip(self) -> None:
        # Its go-live was never recorded: what it cost against the date
        # announced is not knowable, and guessing it would invent a fact.
        roadmap = await read(
            [a_mission(status=ProjectStatus.OPERATIONS, go_live=date(2026, 4, 1))]
        )

        line = roadmap.missions[0]
        assert (line.slippage_days, line.is_late) == (None, False)


class TestTheWindow:
    async def test_it_rolls_from_the_month_before_when_nobody_says_otherwise(
        self,
    ) -> None:
        # Six months ahead of a Friday in September, plus August for context.
        roadmap = await read([a_mission()], from_day=None, to_day=None)

        assert (roadmap.from_day, roadmap.to_day) == (
            date(2026, 8, 1),
            date(2027, 2, 28),
        )

    async def test_a_window_given_by_hand_wins_over_the_span(self) -> None:
        roadmap = await read(
            [a_mission()], from_day=date(2026, 1, 1), to_day=date(2026, 12, 31)
        )

        assert (roadmap.from_day, roadmap.to_day) == (
            date(2026, 1, 1),
            date(2026, 12, 31),
        )

    async def test_a_window_already_over_projects_nothing(self) -> None:
        roadmap = await read(
            [a_mission()],
            entries=entries_on(10, [date(2025, 3, 2)]),
            phases={10: {ProjectStatus.DEVELOPMENT: date(2025, 3, 2)}},
            from_day=date(2025, 1, 1),
            to_day=date(2025, 12, 31),
        )

        [line] = roadmap.missions
        assert all(s.kind is not SegmentKind.PROJECTED for s in line.segments)

    async def test_a_window_read_upside_down_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            await read([a_mission()], from_day=TO_DAY, to_day=FROM_DAY)
