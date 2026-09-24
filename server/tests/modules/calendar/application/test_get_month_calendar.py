"""Reading one month of the calendar."""

from src.modules.calendar.application.use_cases.get_month_calendar import (
    GetMonthCalendarUseCase,
)
from src.modules.calendar.domain.services.working_days import DayKind


async def test_a_month_comes_back_whole() -> None:
    calendar = await GetMonthCalendarUseCase().execute(2026, 9)

    assert (calendar.year, calendar.month) == (2026, 9)
    assert len(calendar.days) == 30


async def test_the_count_and_the_days_cannot_disagree() -> None:
    """They travel together so that no caller takes one without the other."""
    calendar = await GetMonthCalendarUseCase().execute(2026, 9)

    worked = sum(1 for day in calendar.days if day.kind is DayKind.WORKING)
    assert calendar.working_days == worked


async def test_a_public_holiday_is_named_and_not_worked() -> None:
    # 14 July 2026, which no screen should offer to declare on.
    calendar = await GetMonthCalendarUseCase().execute(2026, 7)

    bastille = next(day for day in calendar.days if day.day.day == 14)
    assert bastille.kind is DayKind.HOLIDAY
    assert bastille.is_off_day is True
