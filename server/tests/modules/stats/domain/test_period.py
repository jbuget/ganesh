"""The time window statistics are read over."""

from datetime import date

import pytest

from src.modules.stats.domain.entities.period import Period, PeriodRange

# A Thursday, so that the week-long ranges straddle a weekend.
TODAY = date(2026, 9, 17)


def test_today_covers_the_single_day() -> None:
    period = Period.of(PeriodRange.TODAY, TODAY)

    assert period.start == TODAY
    assert period.end == TODAY


def test_yesterday_covers_the_day_before_and_stops_there() -> None:
    period = Period.of(PeriodRange.YESTERDAY, TODAY)

    assert period.start == date(2026, 9, 16)
    assert period.end == date(2026, 9, 16)


@pytest.mark.parametrize(
    ("range_", "expected_start"),
    [
        (PeriodRange.LAST_7_DAYS, date(2026, 9, 11)),
        (PeriodRange.LAST_30_DAYS, date(2026, 8, 19)),
        (PeriodRange.LAST_90_DAYS, date(2026, 6, 20)),
    ],
)
def test_a_rolling_range_ends_today_and_counts_today_in(
    range_: PeriodRange, expected_start: date
) -> None:
    # "The last 7 days" reads as today plus the six before it: the day in
    # progress is the one people come to check.
    period = Period.of(range_, TODAY)

    assert period.start == expected_start
    assert period.end == TODAY


@pytest.mark.parametrize(
    ("range_", "expected_length"),
    [
        (PeriodRange.TODAY, 1),
        (PeriodRange.YESTERDAY, 1),
        (PeriodRange.LAST_7_DAYS, 7),
        (PeriodRange.LAST_30_DAYS, 30),
        (PeriodRange.LAST_90_DAYS, 90),
    ],
)
def test_a_range_lasts_the_number_of_days_it_announces(
    range_: PeriodRange, expected_length: int
) -> None:
    assert Period.of(range_, TODAY).length_in_days == expected_length


def test_the_previous_period_has_the_same_length_and_ends_the_day_before() -> None:
    # Comparing a week against a week: any other length would make the delta
    # unreadable.
    previous = Period.of(PeriodRange.LAST_7_DAYS, TODAY).previous()

    assert previous.start == date(2026, 9, 4)
    assert previous.end == date(2026, 9, 10)
    assert previous.length_in_days == 7


def test_the_period_before_yesterday_is_the_day_before_yesterday() -> None:
    previous = Period.of(PeriodRange.YESTERDAY, TODAY).previous()

    assert previous.start == date(2026, 9, 15)
    assert previous.end == date(2026, 9, 15)


def test_a_period_counts_the_working_days_it_covers() -> None:
    # 11 to 17 September 2026: two weekend days out of seven.
    period = Period.of(PeriodRange.LAST_7_DAYS, TODAY)

    assert period.working_days == 5


def test_a_weekend_period_covers_no_working_day() -> None:
    # Sunday 20 September 2026: nothing is expected of anyone.
    period = Period.of(PeriodRange.TODAY, date(2026, 9, 20))

    assert period.working_days == 0
