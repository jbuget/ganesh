"""Reads one month of the calendar."""

from src.modules.calendar.domain.entities.month_calendar import MonthCalendar
from src.modules.calendar.domain.services.working_days import (
    days_of_month,
    working_days_count,
)


class GetMonthCalendarUseCase:
    """Answers what a month is made of: its days, and how many are worked.

    It orchestrates and decides nothing — which day is a weekend and which is
    a public holiday is the domain's business. What it adds is that the two
    readings are asked for together, so no caller can take one without the
    other.
    """

    async def execute(self, year: int, month: int) -> MonthCalendar:
        return MonthCalendar(
            year=year,
            month=month,
            working_days=working_days_count(year, month),
            days=tuple(days_of_month(year, month)),
        )
