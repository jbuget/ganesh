"""Reading a month the way a model writes one: « 2026-09 », or nothing at all."""

from datetime import date

from src.shared.utils import clock


def month_asked(month: str | None) -> date | None:
    """The first day of the month asked for, or nothing when it does not read.

    Nothing asked is the month it is in Paris: a call made at half past
    midnight asks about the month the caller is living, not the one UTC is
    still on.
    """
    if month is None:
        today = clock.today()
        return date(today.year, today.month, 1)
    try:
        year, number = month.strip().split("-")
        return date(int(year), int(number), 1)
    except (ValueError, TypeError):
        return None
