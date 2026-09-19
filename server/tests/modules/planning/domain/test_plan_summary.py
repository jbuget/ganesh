"""What a whole projection says in one line."""

from datetime import date

from src.modules.planning.domain.entities.workload_plan import (
    PersonPlan,
    PlanBlocker,
    ProjectedMission,
    WeeklyLoad,
)
from src.modules.planning.domain.services.plan_summary import is_late, summarise

LANDS_ON = date(2026, 10, 16)


def a_landing(
    project_id: int = 10,
    ends_on: date | None = LANDS_ON,
    blocker: PlanBlocker | None = None,
) -> ProjectedMission:
    return ProjectedMission(
        project_id=project_id,
        remaining_days=5.0,
        scheduled_days=5.0,
        ends_on=ends_on,
        blocker=blocker,
    )


def a_person(user_id: int = 1, free: float = 3.0) -> PersonPlan:
    return PersonPlan(
        user_id=user_id,
        weeks=[
            WeeklyLoad(
                week=date(2026, 10, 12), capacity=5.0, booked=5.0 - free, projected=0.0
            )
        ],
    )


class TestLateness:
    def test_landing_well_past_the_date_announced_is_late(self) -> None:
        assert is_late(a_landing(), date(2026, 10, 1)) is True

    def test_a_day_or_two_over_is_not_worth_crying_about(self) -> None:
        assert is_late(a_landing(), date(2026, 10, 14)) is False

    def test_landing_early_is_never_late(self) -> None:
        assert is_late(a_landing(), date(2026, 11, 1)) is False

    def test_a_mission_with_no_date_announced_cannot_be_late(self) -> None:
        assert is_late(a_landing(), None) is False

    def test_a_mission_that_never_lands_is_not_counted_late(self) -> None:
        """It is not late by a measurable amount: it is blocked, and the
        summary counts it there."""
        assert is_late(a_landing(ends_on=None), date(2026, 10, 1)) is False


class TestSummary:
    def test_it_counts_what_the_projection_lands(self) -> None:
        summary = summarise(
            [(a_landing(10), None), (a_landing(20, ends_on=None), None)], []
        )

        assert summary.planned == 1

    def test_it_counts_what_lands_past_the_date_announced(self) -> None:
        summary = summarise(
            [(a_landing(10), date(2026, 10, 1)), (a_landing(20), date(2026, 11, 1))], []
        )

        assert summary.late == 1

    def test_it_calls_out_what_nobody_is_on_among_the_blocked(self) -> None:
        """The one blockage the screen itself can lift."""
        summary = summarise(
            [
                (a_landing(10, ends_on=None, blocker=PlanBlocker.NO_ASSIGNEE), None),
                (a_landing(20, ends_on=None, blocker=PlanBlocker.NO_ESTIMATE), None),
            ],
            [],
        )

        assert (summary.blocked, summary.unassigned) == (2, 1)

    def test_it_totals_the_capacity_nobody_took(self) -> None:
        summary = summarise([], [a_person(1, free=3.0), a_person(2, free=2.5)])

        assert summary.free_days == 5.5

    def test_an_empty_projection_summarises_to_nothing(self) -> None:
        summary = summarise([], [])

        assert (summary.planned, summary.late, summary.blocked) == (0, 0, 0)
