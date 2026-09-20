"""The bounds of the month a numéro covers.

Held in one place because two readings depend on it agreeing with itself: the
slice of register a numéro is built from, and the day past which an announced
date counts as missed.
"""

from calendar import monthrange
from datetime import date, datetime, time


def first_day(month: date) -> date:
    """The day the month opens on, whichever day of it was handed over."""
    return month.replace(day=1)


def last_day(month: date) -> date:
    """The day the month closes on."""
    _, length = monthrange(month.year, month.month)
    return month.replace(day=length)


def bounds(month: date) -> tuple[datetime, datetime]:
    """The month as an instant to an instant, both ends included.

    A numéro covers what happened during the month, and nothing of the day it
    was published: reading a month again a year later must give what it gave.
    """
    return (
        datetime.combine(first_day(month), time.min),
        datetime.combine(last_day(month), time.max),
    )
