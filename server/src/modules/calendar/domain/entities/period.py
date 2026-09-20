"""The time window a screen reads over.

It lives in `calendar` rather than beside any one screen: the statistics and
the activity summary both read a window, and a window that each of them
defined for itself would end up saying two different things about the same
fortnight.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum

from src.modules.calendar.domain.services.working_days import working_days_between


class PeriodRange(StrEnum):
    """The windows the screens offer.

    A closed catalogue rather than two free dates: a dashboard is read at a
    glance, and the comparison against the previous period only means
    something between windows of the same nature.

    Two families live here. The **rolling** ones end today and count back a
    fixed number of days. The **anchored** ones open on a Monday or on a
    first of the month: read on a Monday morning, « last week » means Monday
    to Sunday, and the last seven days would cut the weekend in two.
    """

    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    THIS_WEEK = "this_week"
    LAST_WEEK = "last_week"
    LAST_TWO_WEEKS = "last_two_weeks"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"


#: How many days each rolling window spans, today counted in.
_ROLLING_LENGTHS: dict[PeriodRange, int] = {
    PeriodRange.LAST_7_DAYS: 7,
    PeriodRange.LAST_30_DAYS: 30,
    PeriodRange.LAST_90_DAYS: 90,
}

#: How far back a week-anchored window steps to find the one before it. A
#: whole number of weeks, so the window keeps landing on a Monday.
_WEEK_STEPS: dict[PeriodRange, int] = {
    PeriodRange.THIS_WEEK: 7,
    PeriodRange.LAST_WEEK: 7,
    PeriodRange.LAST_TWO_WEEKS: 14,
}

#: Windows anchored on a first of the month.
_MONTH_RANGES = frozenset({PeriodRange.THIS_MONTH, PeriodRange.LAST_MONTH})


def _monday_of(day: date) -> date:
    """The Monday that opened the week `day` falls in."""
    return day - timedelta(days=day.weekday())


def _first_of_month(day: date) -> date:
    return day.replace(day=1)


@dataclass(frozen=True)
class Period:
    """A range of days, both bounds included."""

    start: date
    end: date
    #: The named window this was built from, when it was built from one. A
    #: window that knows its name knows how to step back by one: the month
    #: before March is 28 days long, and no arithmetic on lengths finds that.
    range_: PeriodRange | None = None

    @classmethod
    def of(cls, range_: PeriodRange, today: date) -> "Period":
        """Turns a named window into the days it actually covers."""
        start, end = cls._bounds(range_, today)
        return cls(start=start, end=end, range_=range_)

    @staticmethod
    def _bounds(range_: PeriodRange, today: date) -> tuple[date, date]:
        if range_ is PeriodRange.TODAY:
            return today, today
        if range_ is PeriodRange.YESTERDAY:
            yesterday = today - timedelta(days=1)
            return yesterday, yesterday
        # A window still running stops today: what comes after it is a
        # forecast, and forecasts are read on Planification, not here.
        if range_ is PeriodRange.THIS_WEEK:
            return _monday_of(today), today
        if range_ is PeriodRange.LAST_WEEK:
            last_monday = _monday_of(today) - timedelta(days=7)
            return last_monday, last_monday + timedelta(days=6)
        if range_ is PeriodRange.LAST_TWO_WEEKS:
            return (
                _monday_of(today) - timedelta(days=14),
                _monday_of(today) - timedelta(days=1),
            )
        if range_ is PeriodRange.THIS_MONTH:
            return _first_of_month(today), today
        if range_ is PeriodRange.LAST_MONTH:
            last_month = _first_of_month(today) - timedelta(days=1)
            return _first_of_month(last_month), last_month
        length = _ROLLING_LENGTHS[range_]
        return today - timedelta(days=length - 1), today

    @property
    def length_in_days(self) -> int:
        return (self.end - self.start).days + 1

    @property
    def working_days(self) -> int:
        """Days the team was expected in, weekends and holidays excluded."""
        return len(working_days_between(self.start, self.end))

    def previous(self) -> "Period":
        """The window of the same nature that precedes this one.

        Same nature, so the two are comparable. A week steps back a week and
        keeps landing on a Monday; a month steps back to the month before,
        whatever its length. Only a window with no name left to read falls
        back on its own length, which is all it has to go on.
        """
        if self.range_ in _WEEK_STEPS:
            return self._shifted_back(_WEEK_STEPS[self.range_])
        if self.range_ in _MONTH_RANGES:
            return self._previous_month()
        return self._shifted_back(self.length_in_days)

    def _shifted_back(self, days: int) -> "Period":
        step = timedelta(days=days)
        return Period(start=self.start - step, end=self.end - step, range_=self.range_)

    def _previous_month(self) -> "Period":
        """The month before, read over the same stretch of it.

        A month still running is compared against as much of the one before:
        twenty days of September read against thirty-one of August would show
        a collapse that is only a calendar. The 31st has no counterpart in
        February, so the window closes on the last day the month has.
        """
        last_day = _first_of_month(self.start) - timedelta(days=1)
        start = _first_of_month(last_day)
        end = min(last_day, start + timedelta(days=self.end.day - 1))
        return Period(start=start, end=end, range_=self.range_)

    def covers(self, day: date) -> bool:
        return self.start <= day <= self.end
