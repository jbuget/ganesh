"""The stretch of time a roadmap is read over.

A window is a choice, not a setting: the civil year is what a team answers
« et cette année, on livre quoi ? » with, and it is therefore what the screen
opens on.
"""

from datetime import date

from src.shared.exceptions.domain_exceptions import ValidationError


def civil_year_of(day: date) -> tuple[date, date]:
    """The year `day` belongs to, whole."""
    return date(day.year, 1, 1), date(day.year, 12, 31)


def ensure_ordered(from_day: date, to_day: date) -> tuple[date, date]:
    """Refuses a window read upside down. Returns it.

    Swapping the two silently would draw a roadmap nobody asked for, and the
    reader would have no way of telling.
    """
    if to_day < from_day:
        raise ValidationError("A roadmap window ends after it starts.")
    return from_day, to_day
