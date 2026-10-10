"""The window the activity mosaic is drawn over."""

from datetime import date, timedelta

from src.modules.calendar.domain.entities.period import Period


def trailing_year(today: date) -> Period:
    """The year that ends today: 365 days, 366 when it holds a 29th of February.

    It opens the day after today's date of last year, so that the mosaic
    holds exactly one of every day of the calendar rather than a day twice.
    A 29th of February has no date a year earlier: the year then opens on the
    1st of March.
    """
    try:
        a_year_ago = today.replace(year=today.year - 1)
    except ValueError:
        a_year_ago = date(today.year - 1, 2, 28)
    return Period(start=a_year_ago + timedelta(days=1), end=today)
