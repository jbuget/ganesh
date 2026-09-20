"""Which months a window closes, and can therefore be late in validating."""

from datetime import date

from src.modules.calendar.domain.entities.period import Period, PeriodRange
from src.modules.stats.domain.services.month_closing import closed_months_covered_by

# A Thursday, so that the week-long ranges straddle a weekend.
TODAY = date(2026, 9, 17)


def test_a_window_inside_a_running_month_closes_no_month() -> None:
    # The last seven days of a month still running: nothing is due yet.
    period = Period.of(PeriodRange.LAST_7_DAYS, TODAY)

    assert closed_months_covered_by(period, TODAY) == []


def test_a_window_reaching_back_closes_the_months_it_covers() -> None:
    # 19 August to 17 September 2026: August is over, September is not.
    period = Period.of(PeriodRange.LAST_30_DAYS, TODAY)

    assert closed_months_covered_by(period, TODAY) == [date(2026, 8, 1)]


def test_a_long_window_closes_every_month_behind_it() -> None:
    # 20 June to 17 September 2026: June, July and August are all over.
    period = Period.of(PeriodRange.LAST_90_DAYS, TODAY)

    assert closed_months_covered_by(period, TODAY) == [
        date(2026, 6, 1),
        date(2026, 7, 1),
        date(2026, 8, 1),
    ]


def test_the_month_that_just_ended_is_closed_on_the_first_of_the_next() -> None:
    # 1 September 2026: August closed yesterday, and is due.
    first_of_month = date(2026, 9, 1)
    period = Period.of(PeriodRange.LAST_7_DAYS, first_of_month)

    assert closed_months_covered_by(period, first_of_month) == [date(2026, 8, 1)]
