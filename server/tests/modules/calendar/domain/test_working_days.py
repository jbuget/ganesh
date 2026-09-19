"""Working days, weekends and French public holidays."""

from datetime import date

import pytest

from src.modules.calendar.domain.services.working_days import (
    DayKind,
    classify_day,
    days_of_month,
    working_days_between,
    working_days_count,
)

# Feries 2026 utilises ici : 1er janvier, 6 avril (lundi de Paques),
# 1er mai, 14 juillet, 25 decembre.


@pytest.mark.parametrize("day", [date(2026, 9, 12), date(2026, 9, 13)])
def test_a_weekend_day_is_flagged_as_weekend(day: date) -> None:
    assert classify_day(day) is DayKind.WEEKEND


def test_a_public_holiday_is_flagged_as_holiday() -> None:
    assert classify_day(date(2026, 5, 1)) is DayKind.HOLIDAY


def test_a_regular_weekday_is_a_working_day() -> None:
    assert classify_day(date(2026, 9, 15)) is DayKind.WORKING


def test_christmas_is_a_holiday() -> None:
    assert classify_day(date(2026, 12, 25)) is DayKind.HOLIDAY


def test_a_holiday_falling_on_a_weekend_is_reported_as_a_holiday() -> None:
    """15 August 2026 falls on a Saturday: the holiday kind wins on screen."""
    assert classify_day(date(2026, 8, 15)) is DayKind.HOLIDAY


def test_a_month_lists_all_its_days() -> None:
    days = days_of_month(2026, 9)

    assert len(days) == 30
    assert days[0].day == date(2026, 9, 1)
    assert days[-1].day == date(2026, 9, 30)


def test_february_of_a_leap_year_has_twenty_nine_days() -> None:
    assert len(days_of_month(2028, 2)) == 29


def test_each_day_of_the_month_carries_its_kind() -> None:
    days = {day.day: day.kind for day in days_of_month(2026, 5)}

    assert days[date(2026, 5, 1)] is DayKind.HOLIDAY
    assert days[date(2026, 5, 2)] is DayKind.WEEKEND
    assert days[date(2026, 5, 4)] is DayKind.WORKING


def test_working_days_count_excludes_weekends_and_holidays() -> None:
    """May 2026: 31 days, 10 weekend days, 3 holidays falling on a weekday."""
    days = days_of_month(2026, 5)
    expected = sum(1 for day in days if day.kind is DayKind.WORKING)

    assert working_days_count(2026, 5) == expected
    assert working_days_count(2026, 5) < 31


class TestWorkingDaysBetween:
    def test_a_window_keeps_only_the_working_days_in_order(self) -> None:
        """A week from Monday to Sunday leaves five days."""
        days = working_days_between(date(2026, 9, 14), date(2026, 9, 20))

        assert days == [date(2026, 9, d) for d in (14, 15, 16, 17, 18)]

    def test_a_holiday_is_left_out_of_the_window(self) -> None:
        """14 July 2026 falls on a Tuesday."""
        days = working_days_between(date(2026, 7, 13), date(2026, 7, 15))

        assert days == [date(2026, 7, 13), date(2026, 7, 15)]

    def test_a_window_that_ends_before_it_starts_is_empty(self) -> None:
        assert working_days_between(date(2026, 9, 18), date(2026, 9, 17)) == []
