"""The time window statistics are read over."""

from datetime import date

import pytest

from src.modules.calendar.domain.entities.period import Period, PeriodRange

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


# --- Anchored windows --------------------------------------------------------
# A rolling week and a calendar week do not answer the same question: read on a
# Monday morning, « last week » means Monday to Sunday, never « the last seven
# days », which cuts the weekend in two and straddles two weeks.


@pytest.mark.parametrize(
    ("range_", "expected_start", "expected_end"),
    [
        # TODAY is a Thursday: this week opened on Monday the 14th.
        (PeriodRange.THIS_WEEK, date(2026, 9, 14), TODAY),
        (PeriodRange.LAST_WEEK, date(2026, 9, 7), date(2026, 9, 13)),
        (PeriodRange.LAST_TWO_WEEKS, date(2026, 8, 31), date(2026, 9, 13)),
        (PeriodRange.THIS_MONTH, date(2026, 9, 1), TODAY),
        (PeriodRange.LAST_MONTH, date(2026, 8, 1), date(2026, 8, 31)),
    ],
)
def test_an_anchored_range_opens_on_its_anchor(
    range_: PeriodRange, expected_start: date, expected_end: date
) -> None:
    period = Period.of(range_, TODAY)

    assert period.start == expected_start
    assert period.end == expected_end


@pytest.mark.parametrize(
    "range_",
    [PeriodRange.THIS_WEEK, PeriodRange.THIS_MONTH],
)
def test_a_window_still_running_stops_today(range_: PeriodRange) -> None:
    # Nothing is read past today: what comes after is a forecast, and the
    # Planification screen is where forecasts belong.
    assert Period.of(range_, TODAY).end == TODAY


def test_a_week_opened_on_a_monday_covers_that_monday_alone() -> None:
    monday = date(2026, 9, 14)

    period = Period.of(PeriodRange.THIS_WEEK, monday)

    assert period.start == monday
    assert period.end == monday


def test_a_month_read_on_its_first_day_covers_that_day_alone() -> None:
    first = date(2026, 9, 1)

    period = Period.of(PeriodRange.THIS_MONTH, first)

    assert period.start == first
    assert period.end == first


@pytest.mark.parametrize(
    ("range_", "expected_start", "expected_end"),
    [
        (PeriodRange.THIS_WEEK, date(2026, 9, 7), date(2026, 9, 10)),
        (PeriodRange.LAST_WEEK, date(2026, 8, 31), date(2026, 9, 6)),
        (PeriodRange.LAST_TWO_WEEKS, date(2026, 8, 17), date(2026, 8, 30)),
        (PeriodRange.THIS_MONTH, date(2026, 8, 1), date(2026, 8, 17)),
        (PeriodRange.LAST_MONTH, date(2026, 7, 1), date(2026, 7, 31)),
    ],
)
def test_the_window_before_an_anchored_one_is_anchored_too(
    range_: PeriodRange, expected_start: date, expected_end: date
) -> None:
    # Stepping back by a length would compare September against 31 days of
    # August and read a fall that never happened.
    previous = Period.of(range_, TODAY).previous()

    assert previous.start == expected_start
    assert previous.end == expected_end


def test_a_running_month_compares_against_the_same_stretch_of_the_one_before() -> None:
    # Twenty days of September read against thirty-one of August would show a
    # collapse that is only a calendar.
    period = Period.of(PeriodRange.THIS_MONTH, date(2026, 9, 20))

    previous = period.previous()

    assert previous.start == date(2026, 8, 1)
    assert previous.end == date(2026, 8, 20)


def test_a_running_month_longer_than_the_one_before_stops_at_its_last_day() -> None:
    # 31 March has no counterpart in February: the window closes on the 28th
    # rather than spilling into March.
    period = Period.of(PeriodRange.THIS_MONTH, date(2026, 3, 31))

    previous = period.previous()

    assert previous.start == date(2026, 2, 1)
    assert previous.end == date(2026, 2, 28)


def test_the_month_before_january_is_december_of_the_year_before() -> None:
    period = Period.of(PeriodRange.LAST_MONTH, date(2026, 1, 15))

    assert period.start == date(2025, 12, 1)
    assert period.end == date(2025, 12, 31)


def test_a_period_remembers_the_range_it_was_built_from() -> None:
    # Without it, a window cannot know that the month before March is 28 days.
    assert Period.of(PeriodRange.LAST_MONTH, TODAY).range_ is PeriodRange.LAST_MONTH


def test_a_period_built_by_hand_steps_back_by_its_own_length() -> None:
    # No range to read: the only thing left to go on is how long it lasts.
    period = Period(start=date(2026, 9, 10), end=date(2026, 9, 12))

    previous = period.previous()

    assert previous.start == date(2026, 9, 7)
    assert previous.end == date(2026, 9, 9)
