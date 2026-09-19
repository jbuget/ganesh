"""Statistics routes: the dashboard of a window."""

from datetime import date

from fastapi import APIRouter, Depends, Query

from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.stats.application.dtos.statistics_dto import StatisticsQuery
from src.modules.stats.application.use_cases.compute_statistics import (
    ComputeStatisticsUseCase,
)
from src.modules.stats.domain.entities.period import PeriodRange
from src.modules.stats.presentation.api.mappers.statistics_mapper import (
    to_statistics_response,
)
from src.modules.stats.presentation.api.schemas.statistics_schemas import (
    StatisticsResponse,
)
from src.modules.stats.presentation.dependencies import get_compute_statistics_use_case
from src.modules.users.domain.entities.user import User

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatisticsResponse, operation_id="getStatistics")
async def get_statistics(
    range_: PeriodRange = Query(PeriodRange.LAST_30_DAYS, alias="range"),
    _: User = Depends(get_current_user),
    use_case: ComputeStatisticsUseCase = Depends(get_compute_statistics_use_case),
) -> StatisticsResponse:
    """The figures of one window. Open to the whole team.

    Everyone reads the same dashboard, those who declared nothing named among
    the rest: a collective coverage rate only moves when each person can see
    their own part in it.
    """
    statistics = await use_case.execute(
        StatisticsQuery(range_=range_, today=date.today())
    )
    return to_statistics_response(statistics, range_=range_)
