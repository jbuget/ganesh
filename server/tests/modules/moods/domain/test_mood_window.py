"""When a mood may still be posted."""

from datetime import date

import pytest

from src.modules.moods.domain.services.mood_window import (
    ensure_day_is_open,
    open_days,
    previous_working_day,
    window_days,
)
from src.shared.exceptions.domain_exceptions import ValidationError

TUESDAY = date(2026, 9, 15)
MONDAY = date(2026, 9, 14)
FRIDAY = date(2026, 9, 11)
SATURDAY = date(2026, 9, 12)


def test_the_day_before_a_tuesday_is_the_monday() -> None:
    assert previous_working_day(TUESDAY) == MONDAY


def test_the_day_before_a_monday_is_the_friday() -> None:
    """Counted in working days: otherwise Friday could never be answered for."""
    assert previous_working_day(MONDAY) == FRIDAY


def test_the_day_before_skips_a_public_holiday() -> None:
    #: 14 July 2026 falls on a Tuesday.
    assert previous_working_day(date(2026, 7, 15)) == date(2026, 7, 13)


def test_a_mood_is_posted_on_today_or_the_working_day_before() -> None:
    assert open_days(TUESDAY) == [TUESDAY, MONDAY]


def test_a_weekend_opens_the_friday_alone() -> None:
    assert open_days(SATURDAY) == [FRIDAY]


def test_today_is_accepted() -> None:
    ensure_day_is_open(TUESDAY, today=TUESDAY)


def test_the_working_day_before_is_accepted() -> None:
    ensure_day_is_open(MONDAY, today=TUESDAY)


def test_a_day_further_back_is_refused() -> None:
    with pytest.raises(ValidationError, match="closed"):
        ensure_day_is_open(FRIDAY, today=TUESDAY)


def test_a_day_to_come_is_refused() -> None:
    with pytest.raises(ValidationError, match="not happened yet"):
        ensure_day_is_open(date(2026, 9, 16), today=TUESDAY)


def test_a_weekend_is_refused() -> None:
    with pytest.raises(ValidationError, match="weekend"):
        ensure_day_is_open(SATURDAY, today=SATURDAY)


def test_a_public_holiday_is_refused() -> None:
    with pytest.raises(ValidationError, match="public holiday"):
        ensure_day_is_open(date(2026, 7, 14), today=date(2026, 7, 14))


def test_the_window_holds_the_working_days_alone_most_recent_first() -> None:
    days = window_days(TUESDAY, span=14)

    assert days[0] == TUESDAY
    assert days[-1] == date(2026, 9, 2)
    assert SATURDAY not in days
    assert len(days) == 10
