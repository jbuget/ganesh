"""Activity routes: who did what over a window, and on what."""

from datetime import date

from fastapi import APIRouter, Depends, Query

from src.modules.activity.application.dtos.activity_dto import ActivityQuery
from src.modules.activity.application.use_cases.get_activity_summary import (
    GetActivitySummaryUseCase,
)
from src.modules.activity.presentation.api.mappers.activity_mapper import (
    to_activity_summary_response,
)
from src.modules.activity.presentation.api.schemas.activity_schemas import (
    ActivitySummaryResponse,
)
from src.modules.activity.presentation.dependencies import get_activity_summary_use_case
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.calendar.domain.entities.period import PeriodRange
from src.modules.users.domain.entities.user import User

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("", response_model=ActivitySummaryResponse, operation_id="getActivity")
async def get_activity_summary(
    range_: PeriodRange = Query(PeriodRange.LAST_WEEK, alias="range"),
    _: User = Depends(get_current_user),
    use_case: GetActivitySummaryUseCase = Depends(get_activity_summary_use_case),
) -> ActivitySummaryResponse:
    """The matrix of one window. Open to the whole team.

    Everyone reads the same figures, and everyone is named in them. The
    reading is retrospective: a window still running stops today, and what
    comes after it is read on Planification.
    """
    summary = await use_case.execute(ActivityQuery(range_=range_, today=date.today()))
    return to_activity_summary_response(summary, range_=range_)
