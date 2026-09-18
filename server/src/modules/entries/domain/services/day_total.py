"""Rules about how full a working day is."""

from collections.abc import Iterable

#: Capacity of a working day, expressed in days.
FULL_DAY: float = 1.0


def day_total(values: Iterable[float]) -> float:
    """Sum of one day's entries."""
    return round(sum(values), 2)


def exceeds_one_day(values: Iterable[float]) -> bool:
    """Tells whether the day goes over the capacity of a working day.

    It is a warning, not a block: entry often happens in two goes.
    """
    return day_total(values) > FULL_DAY


def remaining_capacity(values: Iterable[float]) -> float:
    """What is left to enter on the day, never negative."""
    return max(0.0, round(FULL_DAY - day_total(values), 2))
