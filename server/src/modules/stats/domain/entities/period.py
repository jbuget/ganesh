"""The time window statistics are read over."""

from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum

from src.modules.calendar.domain.services.working_days import working_days_between


class PeriodRange(StrEnum):
    """The windows the screen offers.

    A closed catalogue rather than two free dates: a dashboard is read at a
    glance, and the comparison against the previous period only means
    something between windows of the same length.
    """

    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"


#: How many days each rolling window spans, today counted in.
_ROLLING_LENGTHS: dict[PeriodRange, int] = {
    PeriodRange.LAST_7_DAYS: 7,
    PeriodRange.LAST_30_DAYS: 30,
    PeriodRange.LAST_90_DAYS: 90,
}


@dataclass(frozen=True)
class Period:
    """A range of days, both bounds included."""

    start: date
    end: date

    @classmethod
    def of(cls, range_: PeriodRange, today: date) -> "Period":
        """Turns a named window into the days it actually covers."""
        if range_ is PeriodRange.TODAY:
            return cls(start=today, end=today)
        if range_ is PeriodRange.YESTERDAY:
            yesterday = today - timedelta(days=1)
            return cls(start=yesterday, end=yesterday)
        length = _ROLLING_LENGTHS[range_]
        return cls(start=today - timedelta(days=length - 1), end=today)

    @property
    def length_in_days(self) -> int:
        return (self.end - self.start).days + 1

    @property
    def working_days(self) -> int:
        """Days the team was expected in, weekends and holidays excluded."""
        return working_days_between(self.start, self.end)

    def previous(self) -> "Period":
        """The window of the same length that ends the day before this one.

        Same length, so the two are comparable; adjacent, so nothing falls
        between the two and escapes the reading.
        """
        end = self.start - timedelta(days=1)
        return Period(start=end - timedelta(days=self.length_in_days - 1), end=end)

    def covers(self, day: date) -> bool:
        return self.start <= day <= self.end
