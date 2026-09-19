"""Drawing one mission's bar: what happened, what is supposed, what runs."""

from datetime import date

from src.modules.planning.domain.entities.roadmap import SegmentKind
from src.modules.planning.domain.services.roadmap_drawing import draw_segments
from src.modules.projects.domain.entities.project import ProjectStatus

TODAY = date(2026, 9, 18)
WINDOW_START = date(2026, 1, 1)
WINDOW_END = date(2026, 12, 31)


def segments(
    status: ProjectStatus | None = ProjectStatus.DEVELOPMENT,
    phases: dict[ProjectStatus, date] | None = None,
    first_declared: date | None = None,
    last_declared: date | None = None,
    projected_end: date | None = None,
    is_active: bool = True,
):
    return draw_segments(
        status=status,
        phases_reached=phases or {},
        first_declared=first_declared,
        last_declared=last_declared,
        projected_end=projected_end,
        today=TODAY,
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        is_active=is_active,
    )


class TestTheLivedPart:
    def test_a_mission_with_dated_phases_draws_one_segment_per_phase(self) -> None:
        drawn = segments(
            status=ProjectStatus.DEVELOPMENT,
            phases={
                ProjectStatus.EXPLORATION: date(2026, 3, 2),
                ProjectStatus.SCOPING: date(2026, 4, 1),
                ProjectStatus.DEVELOPMENT: date(2026, 5, 4),
            },
        )

        assert [(s.status, s.starts_on, s.ends_on) for s in drawn] == [
            (ProjectStatus.EXPLORATION, date(2026, 3, 2), date(2026, 3, 31)),
            (ProjectStatus.SCOPING, date(2026, 4, 1), date(2026, 5, 3)),
            (ProjectStatus.DEVELOPMENT, date(2026, 5, 4), TODAY),
        ]
        assert all(s.kind is SegmentKind.LIVED for s in drawn)

    def test_phases_are_ordered_by_date_so_a_step_back_still_reads(self) -> None:
        # Nothing forbids moving backwards, and the date kept is the first
        # time a phase was entered: chronology is what orders the bar.
        drawn = segments(
            status=ProjectStatus.DEVELOPMENT,
            phases={
                ProjectStatus.VALIDATION: date(2026, 4, 1),
                ProjectStatus.DEVELOPMENT: date(2026, 3, 2),
            },
        )

        assert [s.status for s in drawn] == [
            ProjectStatus.DEVELOPMENT,
            ProjectStatus.VALIDATION,
        ]

    def test_two_phases_crossed_the_same_day_leave_no_empty_segment(self) -> None:
        drawn = segments(
            phases={
                ProjectStatus.EXPLORATION: date(2026, 3, 2),
                ProjectStatus.SCOPING: date(2026, 3, 2),
            },
        )

        assert [s.status for s in drawn] == [ProjectStatus.SCOPING]

    def test_time_declared_before_the_first_dated_phase_opens_the_bar(self) -> None:
        # The detail of what came before was never recorded: it is carried by
        # the first phase known rather than invented.
        drawn = segments(
            phases={ProjectStatus.DEVELOPMENT: date(2026, 5, 4)},
            first_declared=date(2026, 2, 10),
        )

        assert drawn[0].starts_on == date(2026, 2, 10)
        assert drawn[0].status is ProjectStatus.DEVELOPMENT

    def test_a_mission_that_never_changed_phase_draws_one_segment(self) -> None:
        drawn = segments(
            status=ProjectStatus.SCOPING,
            first_declared=date(2026, 6, 1),
            last_declared=date(2026, 9, 1),
        )

        assert [(s.status, s.starts_on, s.ends_on) for s in drawn] == [
            (ProjectStatus.SCOPING, date(2026, 6, 1), TODAY)
        ]

    def test_a_mission_with_nothing_behind_it_draws_no_lived_segment(self) -> None:
        assert segments() == []

    def test_an_archived_mission_stops_on_its_last_declared_day(self) -> None:
        drawn = segments(
            phases={ProjectStatus.DEVELOPMENT: date(2026, 1, 5)},
            first_declared=date(2026, 1, 5),
            last_declared=date(2026, 6, 30),
            is_active=False,
        )

        assert drawn[-1].ends_on == date(2026, 6, 30)


class TestTheProjectedPart:
    def test_a_landing_adds_a_projected_segment_after_today(self) -> None:
        drawn = segments(
            phases={ProjectStatus.DEVELOPMENT: date(2026, 5, 4)},
            projected_end=date(2026, 11, 20),
        )

        assert drawn[-1].kind is SegmentKind.PROJECTED
        assert drawn[-1].starts_on == date(2026, 9, 19)
        assert drawn[-1].ends_on == date(2026, 11, 20)

    def test_a_mission_never_started_projects_from_today(self) -> None:
        drawn = segments(projected_end=date(2026, 10, 2))

        assert [(s.kind, s.starts_on) for s in drawn] == [
            (SegmentKind.PROJECTED, TODAY)
        ]

    def test_a_mission_landing_nowhere_carries_no_projected_segment(self) -> None:
        drawn = segments(
            phases={ProjectStatus.DEVELOPMENT: date(2026, 5, 4)}, projected_end=None
        )

        assert [s.kind for s in drawn] == [SegmentKind.LIVED]

    def test_an_archived_mission_is_never_projected(self) -> None:
        drawn = segments(projected_end=date(2026, 11, 20), is_active=False)

        assert drawn == []


class TestAServiceThatRuns:
    def test_operations_closes_the_lived_part_and_runs_to_the_window(self) -> None:
        drawn = segments(
            status=ProjectStatus.OPERATIONS,
            phases={
                ProjectStatus.DEVELOPMENT: date(2026, 3, 2),
                ProjectStatus.OPERATIONS: date(2026, 7, 1),
            },
        )

        assert [(s.kind, s.starts_on, s.ends_on) for s in drawn] == [
            (SegmentKind.LIVED, date(2026, 3, 2), date(2026, 6, 30)),
            (SegmentKind.RUNNING, date(2026, 7, 1), WINDOW_END),
        ]

    def test_a_running_service_is_never_projected(self) -> None:
        drawn = segments(
            status=ProjectStatus.OPERATIONS,
            phases={ProjectStatus.OPERATIONS: date(2026, 7, 1)},
            projected_end=date(2026, 11, 20),
        )

        assert [s.kind for s in drawn] == [SegmentKind.RUNNING]

    def test_a_service_running_since_nobody_recorded_when_opens_at_the_window(
        self,
    ) -> None:
        # Nobody wrote down the day it went live, and it has no history
        # either: it was already running when this window opened. Cutting the
        # rule at the edge says exactly that. Opening it on today would draw
        # a mise en service that never happened — and have the tally above
        # count it.
        drawn = segments(status=ProjectStatus.OPERATIONS)

        assert [(s.kind, s.starts_on, s.ends_on) for s in drawn] == [
            (SegmentKind.RUNNING, WINDOW_START, WINDOW_END)
        ]

    def test_a_service_with_a_history_but_no_go_live_runs_on_from_that_history(
        self,
    ) -> None:
        # Here something *is* known: time was declared up to a day. The rule
        # carries on from where the history stops rather than being dragged
        # back across it.
        drawn = segments(
            status=ProjectStatus.OPERATIONS,
            phases={ProjectStatus.DEVELOPMENT: date(2026, 5, 4)},
            first_declared=date(2026, 5, 4),
            last_declared=date(2026, 9, 1),
        )

        assert [(s.kind, s.starts_on, s.ends_on) for s in drawn] == [
            (SegmentKind.LIVED, date(2026, 5, 4), date(2026, 9, 17)),
            (SegmentKind.RUNNING, TODAY, WINDOW_END),
        ]

    def test_a_service_retired_stops_running_at_its_last_declared_day(self) -> None:
        drawn = segments(
            status=ProjectStatus.OPERATIONS,
            phases={ProjectStatus.OPERATIONS: date(2025, 7, 1)},
            last_declared=date(2026, 2, 28),
            is_active=False,
        )

        assert [(s.kind, s.ends_on) for s in drawn] == [
            (SegmentKind.RUNNING, date(2026, 2, 28))
        ]
