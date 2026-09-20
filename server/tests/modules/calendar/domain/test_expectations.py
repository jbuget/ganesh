"""What a window expects of someone, before anything is declared."""

from datetime import date

from src.modules.calendar.domain.entities.period import Period, PeriodRange
from src.modules.calendar.domain.services.expectations import expected_days

# A Thursday, so that the week-long ranges straddle a weekend.
TODAY = date(2026, 9, 17)


def test_the_team_is_expected_every_working_day_of_the_period() -> None:
    # Five working days between 11 and 17 September 2026, twelve teammates.
    period = Period.of(PeriodRange.LAST_7_DAYS, TODAY)

    assert expected_days(period, people=12) == 60


def test_a_period_without_a_working_day_expects_nothing() -> None:
    # Sunday: nobody owes a half day.
    period = Period.of(PeriodRange.TODAY, date(2026, 9, 20))

    assert expected_days(period, people=12) == 0


def test_a_team_with_nobody_in_it_is_expected_nothing() -> None:
    period = Period.of(PeriodRange.LAST_30_DAYS, TODAY)

    assert expected_days(period, people=0) == 0
