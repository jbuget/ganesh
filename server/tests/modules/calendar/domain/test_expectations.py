"""What a window expects of someone, before anything is declared."""

from datetime import date

from src.modules.calendar.domain.entities.period import Period, PeriodRange
from src.modules.calendar.domain.entities.week_pattern import WeekPattern
from src.modules.calendar.domain.services.expectations import expected_days

# A Thursday, so that the week-long ranges straddle a weekend.
TODAY = date(2026, 9, 17)


def test_a_full_time_teammate_is_expected_every_working_day() -> None:
    # Five working days between 11 and 17 September 2026.
    period = Period.of(PeriodRange.LAST_7_DAYS, TODAY)

    assert expected_days(period) == 5


def test_a_period_without_a_working_day_expects_nothing() -> None:
    # Sunday: nobody owes a half day.
    period = Period.of(PeriodRange.TODAY, date(2026, 9, 20))

    assert expected_days(period) == 0


def test_a_rhythm_takes_its_days_off_out_of_what_is_expected() -> None:
    period = Period.of(PeriodRange.LAST_7_DAYS, TODAY)

    assert expected_days(period, WeekPattern(wednesday=0.0)) == 4


def test_a_half_day_counts_for_a_half() -> None:
    period = Period.of(PeriodRange.LAST_7_DAYS, TODAY)

    assert expected_days(period, WeekPattern(wednesday=0.5)) == 4.5


def test_a_day_off_falling_on_a_public_holiday_is_not_lost_twice() -> None:
    # Whit Monday 2026 falls on 25 May. Somebody who never works on a Monday
    # loses nothing to it; a count made from a number of days a week could
    # not tell that.
    week_of_whit_monday = Period(start=date(2026, 5, 25), end=date(2026, 5, 29))

    assert expected_days(week_of_whit_monday) == 4
    assert expected_days(week_of_whit_monday, WeekPattern(monday=0.0)) == 4
    assert expected_days(week_of_whit_monday, WeekPattern(friday=0.0)) == 3
