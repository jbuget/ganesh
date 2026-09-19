"""How a month is designated."""

from datetime import date


def first_day_of(month: date) -> date:
    """The day that holds a month, whatever day names it.

    A month is designated by any of its days — the screen hands over the one
    it is on. Everything that stores or compares a month agrees on its first
    day, so that the same month is never written, nor looked for, twice.
    """
    return month.replace(day=1)
