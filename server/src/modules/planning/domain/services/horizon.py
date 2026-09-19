"""How far ahead a projection looks.

A horizon is not a setting of the machine: it is how far the team is willing
to believe its own forecast. Six months by default — beyond that, the diaries
hold nothing but weekends and hope.
"""

from calendar import monthrange
from datetime import date, timedelta

from src.shared.exceptions.domain_exceptions import ValidationError

DEFAULT_HORIZON_MONTHS = 6

#: Past this, a projection reads nothing: the capacity it eats into is made of
#: days nobody has declared anything on yet.
MAX_HORIZON_MONTHS = 24


def ensure_readable(months: int) -> int:
    """Refuses a horizon nobody could read anything into. Returns it.

    The one place the bounds are spelled out: a projection and a simulation
    must not be able to disagree on what a legitimate horizon is.
    """
    if not 1 <= months <= MAX_HORIZON_MONTHS:
        raise ValidationError(
            f"A horizon runs from 1 to {MAX_HORIZON_MONTHS} months, not {months}."
        )
    return months


def horizon_end(start: date, months: int = DEFAULT_HORIZON_MONTHS) -> date:
    """The last day a projection starting on `start` may fill."""
    return _months_later(start, ensure_readable(months)) - timedelta(days=1)


def _months_later(day: date, months: int) -> date:
    """The same day of the month, `months` later.

    A month short of that day keeps its last one: six months after 31 August
    is 28 February, not a date that does not exist.
    """
    total = day.month - 1 + months
    year = day.year + total // 12
    month = total % 12 + 1
    return date(year, month, min(day.day, monthrange(year, month)[1]))


def months_to_cover(start: date, end: date) -> int:
    """Months a projection must run for to reach the end of a window.

    A roadmap chooses its window and the projection follows, rather than the
    other way round: nobody reading a year of deliveries thinks in horizons.
    Zero when the window is already over — there is nothing left to suppose —
    and never past what a projection can honestly say.
    """
    if end <= start:
        return 0
    months = (end.year - start.year) * 12 + end.month - start.month + 1
    return min(months, MAX_HORIZON_MONTHS)
