"""Activity routes: who did what over a window, and on what."""

from fastapi import APIRouter, Depends, Query

from src.modules.activity_summary.application.dtos.activity_summary_dto import (
    ActivitySummaryQuery,
)
from src.modules.activity_summary.application.use_cases.get_activity_summary import (
    GetActivitySummaryUseCase,
)
from src.modules.activity_summary.presentation.api.mappers.activity_summary_mapper import (
    to_activity_summary_response,
)
from src.modules.activity_summary.presentation.api.schemas.activity_summary_schemas import (
    ActivitySummaryResponse,
)
from src.modules.activity_summary.presentation.dependencies import (
    get_activity_summary_use_case,
)
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.calendar.domain.entities.period import PeriodRange
from src.modules.users.domain.entities.user import User
from src.shared.utils import clock

router = APIRouter(prefix="/activity-summary", tags=["activity-summary"])


@router.get(
    "", response_model=ActivitySummaryResponse, operation_id="getActivitySummary"
)
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
    summary = await use_case.execute(
        ActivitySummaryQuery(range_=range_, today=clock.today())
    )
    return to_activity_summary_response(summary, range_=range_)
