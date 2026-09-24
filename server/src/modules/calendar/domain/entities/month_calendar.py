"""A month, and what each of its days is worth."""

from dataclasses import dataclass

from src.modules.calendar.domain.services.working_days import CalendarDay


@dataclass(frozen=True)
class MonthCalendar:
    """The days of one month, and how many of them are worked.

    The count travels beside the days rather than being left for the reader to
    derive: every screen that shows a month shows it, and two of them counting
    for themselves is two chances to count differently.
    """

    year: int
    month: int
    working_days: int
    days: tuple[CalendarDay, ...]
