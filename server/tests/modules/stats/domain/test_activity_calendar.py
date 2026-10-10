"""The calendar the activity mosaic is drawn from."""

from datetime import date

from src.modules.calendar.domain.entities.period import Period
from src.modules.stats.domain.services.activity_calendar import activity_calendar

WEEK = Period(start=date(2026, 9, 14), end=date(2026, 9, 17))


def test_every_day_of_the_window_has_its_line_oldest_first() -> None:
    calendar = activity_calendar(WEEK, {})

    assert [entry.day for entry in calendar] == [
        date(2026, 9, 14),
        date(2026, 9, 15),
        date(2026, 9, 16),
        date(2026, 9, 17),
    ]


def test_a_day_the_log_is_silent_about_holds_no_gesture() -> None:
    calendar = activity_calendar(WEEK, {date(2026, 9, 15): 3})

    assert [entry.gestures for entry in calendar] == [0, 3, 0, 0]


def test_a_day_outside_the_window_is_left_out() -> None:
    calendar = activity_calendar(WEEK, {date(2026, 9, 1): 9})

    assert sum(entry.gestures for entry in calendar) == 0
