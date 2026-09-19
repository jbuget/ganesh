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


def test_working_days_between_counts_both_bounds() -> None:
    # Monday 5 to Friday 9 January 2026: five working days, bounds included.
    assert working_days_between(date(2026, 1, 5), date(2026, 1, 9)) == 5


def test_working_days_between_excludes_weekends() -> None:
    # Monday 5 to Sunday 11 January 2026: the weekend does not count.
    assert working_days_between(date(2026, 1, 5), date(2026, 1, 11)) == 5


def test_working_days_between_excludes_public_holidays() -> None:
    # 1 May 2026 falls on a Friday: the week only offers four working days.
    assert working_days_between(date(2026, 4, 27), date(2026, 5, 1)) == 4


def test_working_days_between_spans_months_and_years() -> None:
    # 28 December 2026 to 1 January 2027: 25 December is behind us, but
    # 1 January is a holiday, so only 28, 29, 30 and 31 are worked.
    assert working_days_between(date(2026, 12, 28), date(2027, 1, 1)) == 4


def test_a_single_working_day_counts_as_one() -> None:
    assert working_days_between(date(2026, 1, 5), date(2026, 1, 5)) == 1


def test_a_single_weekend_day_counts_as_none() -> None:
    assert working_days_between(date(2026, 1, 10), date(2026, 1, 10)) == 0


def test_an_inverted_range_holds_no_working_day() -> None:
    # Nothing between the two bounds: the count is zero, not an error.
    assert working_days_between(date(2026, 1, 9), date(2026, 1, 5)) == 0
