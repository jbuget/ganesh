"""What kind of day each day of the month is: working, weekend or holiday.

`holidays` is a deterministic computation library, with no I/O and no
framework: it belongs in the domain, just as `datetime` does.
"""

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum
from functools import lru_cache

import holidays

SATURDAY = 5


class DayKind(StrEnum):
    """What kind of day a calendar day is."""

    WORKING = "working"
    WEEKEND = "weekend"
    HOLIDAY = "holiday"


@dataclass(frozen=True)
class CalendarDay:
    """A day of the month and its kind."""

    day: date
    kind: DayKind
    label: str | None = None

    @property
    def is_off_day(self) -> bool:
        """A non-working day stands out in the entry grid."""
        return self.kind is not DayKind.WORKING


@lru_cache(maxsize=16)
def _french_holidays(year: int) -> dict[date, str]:
    return dict(holidays.country_holidays("FR", years=year))


def holiday_label(day: date) -> str | None:
    """Name of the public holiday, or None if the day is not one."""
    return _french_holidays(day.year).get(day)


def classify_day(day: date) -> DayKind:
    """Works out what kind of day this is.

    A holiday falling on a weekend is reported as a holiday: that is the more
    useful thing to show.
    """
    if holiday_label(day) is not None:
        return DayKind.HOLIDAY
    if day.weekday() >= SATURDAY:
        return DayKind.WEEKEND
    return DayKind.WORKING


def days_of_month(year: int, month: int) -> list[CalendarDay]:
    """Every day of the month, with its kind."""
    _, last_day = monthrange(year, month)
    return [
        CalendarDay(
            day=(day := date(year, month, numero)),
            kind=classify_day(day),
            label=holiday_label(day),
        )
        for numero in range(1, last_day + 1)
    ]


def working_days_count(year: int, month: int) -> int:
    """Number of working days in the month, holidays and weekends excluded."""
    return sum(1 for day in days_of_month(year, month) if day.kind is DayKind.WORKING)


def working_days_between(start: date, end: date) -> int:
    """Number of working days between two dates, both bounds included.

    Unlike `working_days_count`, this one spans any range: a statistics window
    rarely lines up with a month. An inverted range holds nothing, and says so
    with a zero rather than an error: it is a count, not a command.
    """
    if end < start:
        return 0
    days = (end - start).days + 1
    return sum(
        1
        for offset in range(days)
        if classify_day(start + timedelta(days=offset)) is DayKind.WORKING
    )
