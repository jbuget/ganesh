"""The stretch of time a roadmap is read over.

A window is a choice, not a setting of the machine, and the choice it makes is
where to spend the width of the screen. Read over a civil year in September,
two thirds of that width goes to a past nobody is deciding anything about: a
roadmap looks ahead, and the window has to look where the roadmap does.

Hence a rolling window. It opens one month back — enough to see where the
work came from — and runs as many months ahead as one is willing to believe.
"""

from calendar import monthrange
from datetime import date, timedelta

from src.shared.exceptions.domain_exceptions import ValidationError

#: Two quarters ahead. Long enough to hold a delivery and short enough that a
#: fortnight of work is still a fortnight wide on screen.
DEFAULT_ROADMAP_MONTHS = 6

#: Past this, months are so narrow that a bar says nothing but « somewhere in
#: the spring ». The scale, not the projection, is what gives out first.
MAX_ROADMAP_MONTHS = 24


def ensure_readable_span(months: int) -> int:
    """Refuses a span nobody could read a bar in. Returns it."""
    if not 1 <= months <= MAX_ROADMAP_MONTHS:
        raise ValidationError(
            f"A roadmap spans 1 to {MAX_ROADMAP_MONTHS} months, not {months}."
        )
    return months


def rolling_window(
    today: date, months: int = DEFAULT_ROADMAP_MONTHS
) -> tuple[date, date]:
    """The window a roadmap opens on, anchored on today.

    `months` counts what is looked at **ahead**, the month in progress
    included: six months read in September closes at the end of February. The
    month before is thrown in on top, and is not counted — it is context, not
    horizon.

    Both ends land on month boundaries. The scale draws whole months, and a
    window opening on the 18th would leave a stump of a column at each end.
    """
    ensure_readable_span(months)

    opens_on = _first_of_month(today.year, today.month - 1)
    last = _first_of_month(today.year, today.month + months - 1)
    return opens_on, _end_of_month(last)


def ensure_ordered(from_day: date, to_day: date) -> tuple[date, date]:
    """Refuses a window read upside down. Returns it.

    Swapping the two silently would draw a roadmap nobody asked for, and the
    reader would have no way of telling.
    """
    if to_day < from_day:
        raise ValidationError("A roadmap window ends after it starts.")
    return from_day, to_day


def _first_of_month(year: int, month: int) -> date:
    """The first of a month, counted from January whatever the overflow.

    `month` may run past twelve or below one: the caller adds and subtracts
    months without having to think about the year boundary.
    """
    total = year * 12 + month - 1
    return date(total // 12, total % 12 + 1, 1)


def _end_of_month(first: date) -> date:
    return first + timedelta(days=monthrange(first.year, first.month)[1] - 1)
