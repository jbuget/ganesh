"""Wiring of the calendar use cases."""

from src.modules.calendar.application.use_cases.get_month_calendar import (
    GetMonthCalendarUseCase,
)


def get_month_calendar_use_case() -> GetMonthCalendarUseCase:
    """It leans on nothing: the calendar is computed, never stored."""
    return GetMonthCalendarUseCase()
