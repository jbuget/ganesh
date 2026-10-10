"""The calendar the activity mosaic is drawn from."""

from datetime import date, timedelta

from src.modules.calendar.domain.entities.period import Period
from src.modules.stats.domain.entities.statistics import ActivityDay


def activity_calendar(period: Period, gestures: dict[date, int]) -> list[ActivityDay]:
    """One line per day of the window, oldest first, quiet days included.

    The log only holds the days something happened. A calendar with holes
    cannot be drawn, and a day the log is silent about is a day of no gesture,
    not a day nobody knows about.
    """
    return [
        ActivityDay(day=day, gestures=gestures.get(day, 0))
        for day in (
            period.start + timedelta(days=offset)
            for offset in range(period.length_in_days)
        )
    ]
