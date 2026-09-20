"""Statistics routes: the dashboard of a window."""

from fastapi import APIRouter, Depends, Query

from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.api_keys.presentation.dependencies import Caller, open_to_machines
from src.modules.calendar.domain.entities.period import PeriodRange
from src.modules.stats.application.dtos.statistics_dto import StatisticsQuery
from src.modules.stats.application.use_cases.compute_statistics import (
    ComputeStatisticsUseCase,
)
from src.modules.stats.presentation.api.mappers.statistics_mapper import (
    to_statistics_response,
)
from src.modules.stats.presentation.api.schemas.statistics_schemas import (
    StatisticsResponse,
)
from src.modules.stats.presentation.dependencies import get_compute_statistics_use_case
from src.shared.utils import clock

router = APIRouter(prefix="/stats", tags=["stats"])

#: The figures a machine may read: an automatic weekly report, a dashboard
#: outside Ganesh. Figures rather than a register — though it does name who
#: has yet to declare, which is the whole team's to see and so a key's too.
statistics_reader = open_to_machines(ApiKeyScope.STATS_READ)


@router.get("", response_model=StatisticsResponse, operation_id="getStatistics")
async def get_statistics(
    range_: PeriodRange = Query(PeriodRange.LAST_30_DAYS, alias="range"),
    _: Caller = Depends(statistics_reader),
    use_case: ComputeStatisticsUseCase = Depends(get_compute_statistics_use_case),
) -> StatisticsResponse:
    """The figures of one window. Open to the whole team.

    Everyone reads the same dashboard, those who declared nothing named among
    the rest: a collective coverage rate only moves when each person can see
    their own part in it.
    """
    statistics = await use_case.execute(
        StatisticsQuery(range_=range_, today=clock.today())
    )
    return to_statistics_response(statistics, range_=range_)
