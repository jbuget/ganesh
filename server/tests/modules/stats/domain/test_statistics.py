"""What the dashboard figures mean, and how they are worked out."""

import pytest

from src.modules.stats.domain.entities.statistics import (
    Adoption,
    Coverage,
    Freshness,
    MissionShare,
    MonthValidation,
    Registry,
    Teammate,
)


class TestCoverage:
    def test_coverage_is_what_was_declared_over_what_was_expected(self) -> None:
        assert Coverage(declared_days=142, expected_days=163).rate == pytest.approx(
            142 / 163
        )

    def test_a_fully_declared_period_is_covered(self) -> None:
        assert Coverage(declared_days=80, expected_days=80).rate == 1.0

    def test_nothing_expected_makes_the_rate_meaningless(self) -> None:
        # A weekend, or a team with nobody in it: there is no rate to show,
        # and showing a zero would read as a failure that is not one.
        assert Coverage(declared_days=0, expected_days=0).rate is None

    def test_declaring_more_than_expected_is_reported_as_is(self) -> None:
        # Overtime, or a day split across two missions beyond a full day: the
        # dashboard reports rather than caps, an excess is worth seeing.
        assert Coverage(declared_days=90, expected_days=80).rate == pytest.approx(1.125)

    def test_the_missing_days_are_what_is_left_to_declare(self) -> None:
        assert Coverage(declared_days=142, expected_days=163).missing_days == 21

    def test_an_excess_leaves_nothing_missing(self) -> None:
        assert Coverage(declared_days=90, expected_days=80).missing_days == 0

    def test_the_delta_against_another_period_is_told_in_points(self) -> None:
        current = Coverage(declared_days=87, expected_days=100)
        previous = Coverage(declared_days=81, expected_days=100)

        assert current.delta_in_points(previous) == pytest.approx(6.0)

    def test_there_is_no_delta_without_a_comparable_period(self) -> None:
        current = Coverage(declared_days=87, expected_days=100)
        previous = Coverage(declared_days=0, expected_days=0)

        assert current.delta_in_points(previous) is None


class TestFreshness:
    def test_the_median_delay_splits_the_entries_in_two(self) -> None:
        assert Freshness(delays=[0, 1, 2, 3, 40]).median_delay == 2

    def test_an_even_count_averages_the_two_middle_delays(self) -> None:
        assert Freshness(delays=[0, 1, 2, 5]).median_delay == pytest.approx(1.5)

    def test_a_median_ignores_the_one_entry_caught_up_very_late(self) -> None:
        # The median is deliberate: one month-end catch-up must not drag the
        # whole reading with it, the way an average would.
        assert Freshness(delays=[1, 1, 1, 1, 120]).median_delay == 1

    def test_no_entry_at_all_leaves_the_freshness_unknown(self) -> None:
        assert Freshness(delays=[]).median_delay is None

    def test_entries_filled_within_two_days_count_as_day_to_day(self) -> None:
        assert Freshness(delays=[0, 1, 2, 3]).day_to_day_share == pytest.approx(0.75)

    def test_an_entry_caught_up_after_a_fortnight_counts_as_late(self) -> None:
        assert Freshness(delays=[1, 1, 16, 30]).late_share == pytest.approx(0.5)

    def test_shares_are_unknown_when_nothing_was_filled_in(self) -> None:
        assert Freshness(delays=[]).day_to_day_share is None
        assert Freshness(delays=[]).late_share is None


class TestAdoption:
    def test_adoption_is_the_share_of_the_team_that_declared_anything(self) -> None:
        adoption = Adoption(
            contributors=11,
            idle=[Teammate(id=1, display_name="L. Chen")],
        )

        assert adoption.expected_contributors == 12
        assert adoption.rate == pytest.approx(11 / 12)

    def test_a_team_where_everyone_declared_is_fully_on_board(self) -> None:
        assert Adoption(contributors=9, idle=[]).rate == 1.0

    def test_an_empty_team_has_no_adoption_rate(self) -> None:
        assert Adoption(contributors=0, idle=[]).rate is None


class TestMonthValidation:
    def test_validation_is_the_share_of_closed_months_that_were_locked(self) -> None:
        assert MonthValidation(validated=9, due=12).rate == pytest.approx(0.75)

    def test_a_window_covering_no_closed_month_has_nothing_to_report(self) -> None:
        # Seven days in the middle of a month close nothing: the figure is
        # absent rather than zero.
        assert MonthValidation(validated=0, due=0).rate is None


class TestMissionShare:
    def test_a_mission_carries_its_share_of_the_declared_time(self) -> None:
        share = MissionShare(project_id=3, label="Extranet", days=20, total_days=80)

        assert share.share == pytest.approx(0.25)

    def test_a_mission_on_an_empty_period_carries_no_share(self) -> None:
        share = MissionShare(project_id=3, label="Extranet", days=0, total_days=0)

        assert share.share is None


class TestRegistry:
    def test_missions_nobody_booked_time_against_are_counted(self) -> None:
        registry = Registry(active_missions=30, missions_with_time=18, created=2)

        assert registry.missions_without_time == 12

    def test_a_registry_everyone_books_against_leaves_nothing_idle(self) -> None:
        registry = Registry(active_missions=18, missions_with_time=18, created=0)

        assert registry.missions_without_time == 0

    def test_the_share_of_the_registry_actually_in_use_is_told(self) -> None:
        registry = Registry(active_missions=30, missions_with_time=18, created=2)

        assert registry.usage_rate == pytest.approx(0.6)

    def test_an_empty_registry_has_no_usage_rate(self) -> None:
        assert (
            Registry(active_missions=0, missions_with_time=0, created=0).usage_rate
            is None
        )
