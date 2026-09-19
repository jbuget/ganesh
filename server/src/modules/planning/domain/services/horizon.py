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


def horizon_end(start: date, months: int = DEFAULT_HORIZON_MONTHS) -> date:
    """The last day a projection starting on `start` may fill."""
    if months < 1 or months > MAX_HORIZON_MONTHS:
        raise ValidationError(
            f"A horizon runs from 1 to {MAX_HORIZON_MONTHS} months, not {months}."
        )
    return _months_later(start, months) - timedelta(days=1)


def _months_later(day: date, months: int) -> date:
    """The same day of the month, `months` later.

    A month short of that day keeps its last one: six months after 31 August
    is 28 February, not a date that does not exist.
    """
    total = day.month - 1 + months
    year = day.year + total // 12
    month = total % 12 + 1
    return date(year, month, min(day.day, monthrange(year, month)[1]))
