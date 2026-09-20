"""What is asked of the dashboard."""

from dataclasses import dataclass
from datetime import date

from src.modules.calendar.domain.entities.period import PeriodRange


@dataclass(frozen=True)
class StatisticsQuery:
    """A window to read, and the day it is read from.

    `today` is passed in rather than taken from the clock: the whole reading
    hangs on it, and a figure that cannot be pinned to a date cannot be
    tested.
    """

    range_: PeriodRange
    today: date
