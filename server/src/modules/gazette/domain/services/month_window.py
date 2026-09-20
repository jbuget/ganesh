"""The bounds of the month a numéro covers.

Held in one place because two readings depend on it agreeing with itself: the
slice of register a numéro is built from, and the day past which an announced
date counts as missed.
"""

from calendar import monthrange
from datetime import date, datetime, time

from src.shared.utils import clock


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

    Whose month it is has to be said, the register holding instants in UTC:
    it is the team's, so both ends are Paris midnights. Left naive, the last
    two hours of September would be read into October.
    """
    return (
        clock.as_instant(datetime.combine(first_day(month), time.min)),
        clock.as_instant(datetime.combine(last_day(month), time.max)),
    )
