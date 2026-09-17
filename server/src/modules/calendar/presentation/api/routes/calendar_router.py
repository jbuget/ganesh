"""Routes du calendrier : jours ouvres, week-ends et feries."""

from fastapi import APIRouter, Depends, Path

from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.calendar.domain.services.working_days import (
    days_of_month,
    working_days_count,
)
from src.modules.calendar.presentation.api.schemas.calendar_schemas import (
    MonthCalendarResponse,
)
from src.modules.users.domain.entities.user import User

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get(
    "/{year}/{month}",
    response_model=MonthCalendarResponse,
    operation_id="getMonthCalendar",
)
async def get_month_calendar(
    year: int,
    month: int = Path(ge=1, le=12),
    _: User = Depends(get_current_user),
) -> MonthCalendarResponse:
    """Les jours du mois et leur nature."""
    return MonthCalendarResponse(
        year=year,
        month=month,
        working_days=working_days_count(year, month),
        days=[
            {
                "jour": day.jour,
                "kind": day.kind.value,
                "label": day.label,
                "is_off_day": day.is_off_day,
            }
            for day in days_of_month(year, month)
        ],
    )
