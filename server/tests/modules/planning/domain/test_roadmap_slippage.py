"""Whether a mission held the date it announced, and how sure one is of it."""

from datetime import date

from src.modules.planning.domain.entities.workload_plan import ProjectedMission
from src.modules.planning.domain.services.roadmap_slippage import slippage_of

ANNOUNCED = date(2026, 6, 1)


def landing(day: date | None) -> ProjectedMission:
    return ProjectedMission(
        project_id=1, remaining_days=1.0, scheduled_days=1.0, starts_on=day, ends_on=day
    )


class TestAMissionStillToBuild:
    def test_a_projection_landing_past_the_date_slips_by_supposition(self) -> None:
        slipped = slippage_of(None, landing(date(2026, 7, 1)), ANNOUNCED)

        assert (slipped.days, slipped.is_late, slipped.settled) == (30, True, False)

    def test_a_projection_landing_early_does_not_slip(self) -> None:
        slipped = slippage_of(None, landing(date(2026, 5, 1)), ANNOUNCED)

        assert (slipped.days, slipped.is_late) == (-31, False)

    def test_a_day_or_two_over_still_reads_as_on_time(self) -> None:
        # A projection is not a commitment: crying wolf over two days makes
        # the whole screen unbelievable.
        slipped = slippage_of(None, landing(date(2026, 6, 3)), ANNOUNCED)

        assert (slipped.days, slipped.is_late) == (2, False)

    def test_a_mission_landing_nowhere_says_nothing(self) -> None:
        slipped = slippage_of(None, landing(None), ANNOUNCED)

        assert (slipped.days, slipped.is_late) == (None, False)

    def test_a_mission_with_no_projection_at_all_says_nothing(self) -> None:
        slipped = slippage_of(None, None, ANNOUNCED)

        assert (slipped.days, slipped.is_late) == (None, False)


class TestAServiceAlreadyLive:
    def test_a_service_that_went_live_late_slips_as_a_fact(self) -> None:
        # It is not a projection any more: the register holds the day, and the
        # delay is the one thing about this mission nobody can argue with.
        slipped = slippage_of(date(2026, 8, 20), None, ANNOUNCED)

        assert (slipped.days, slipped.is_late, slipped.settled) == (80, True, True)

    def test_a_service_that_went_live_on_time_does_not_slip(self) -> None:
        slipped = slippage_of(date(2026, 5, 28), None, ANNOUNCED)

        assert (slipped.days, slipped.is_late) == (-4, False)

    def test_the_recorded_go_live_wins_over_any_projection(self) -> None:
        # Both should never arrive together — a running service is dropped
        # from the backlog. If they ever did, the fact answers.
        slipped = slippage_of(date(2026, 6, 2), landing(date(2027, 1, 1)), ANNOUNCED)

        assert (slipped.days, slipped.settled) == (1, True)

    def test_a_service_live_but_never_announced_slips_by_nothing(self) -> None:
        # Nothing was promised, so nothing was missed.
        slipped = slippage_of(date(2026, 8, 20), None, None)

        assert (slipped.days, slipped.is_late) == (None, False)
