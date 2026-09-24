"""Calendar routes: working days, weekends and holidays."""

from fastapi import APIRouter, Depends, Path

from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.calendar.application.use_cases.get_month_calendar import (
    GetMonthCalendarUseCase,
)
from src.modules.calendar.domain.entities.month_calendar import MonthCalendar
from src.modules.calendar.presentation.api.schemas.calendar_schemas import (
    CalendarDaySchema,
    MonthCalendarResponse,
)
from src.modules.calendar.presentation.dependencies import get_month_calendar_use_case
from src.modules.users.domain.entities.user import User

router = APIRouter(prefix="/calendar", tags=["calendar"])


def to_month_calendar_response(calendar: MonthCalendar) -> MonthCalendarResponse:
    return MonthCalendarResponse(
        year=calendar.year,
        month=calendar.month,
        working_days=calendar.working_days,
        days=[
            CalendarDaySchema(
                day=day.day,
                kind=day.kind.value,
                label=day.label,
                is_off_day=day.is_off_day,
            )
            for day in calendar.days
        ],
    )


@router.get(
    "/{year}/{month}",
    response_model=MonthCalendarResponse,
    operation_id="getMonthCalendar",
)
async def get_month_calendar(
    year: int,
    month: int = Path(ge=1, le=12),
    _: User = Depends(get_current_user),
    use_case: GetMonthCalendarUseCase = Depends(get_month_calendar_use_case),
) -> MonthCalendarResponse:
    """The days of the month and their kind."""
    return to_month_calendar_response(await use_case.execute(year, month))
