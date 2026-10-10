"""The weeks a curve of the coverage is drawn over."""

from datetime import date, timedelta

from src.modules.calendar.domain.entities.period import Period


def trailing_weeks(today: date, count: int) -> list[Period]:
    """The last `count` weeks, oldest first, each opening on a Monday.

    The week running stops today: what comes after it is a forecast, and a
    forecast is not owed yet.
    """
    this_monday = today - timedelta(days=today.weekday())
    weeks: list[Period] = []

    for weeks_back in range(count - 1, -1, -1):
        monday = this_monday - timedelta(weeks=weeks_back)
        weeks.append(Period(start=monday, end=min(monday + timedelta(days=6), today)))
    return weeks
