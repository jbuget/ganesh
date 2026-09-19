"""Routes of the workload plan.

The plan is read by the whole team, as the board is: knowing what is coming
and who is taken is everybody's business. Only what writes stays a manager's
privilege, and a projection writes nothing.
"""

from fastapi import APIRouter, Depends, Query

from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.planning.application.dtos.workload_dto import (
    PersonLoadRow,
    PlannedMissionRow,
    WorkloadReading,
)
from src.modules.planning.application.use_cases.get_workload_plan import (
    GetWorkloadPlanUseCase,
)
from src.modules.planning.domain.services.horizon import (
    DEFAULT_HORIZON_MONTHS,
    MAX_HORIZON_MONTHS,
)
from src.modules.planning.presentation.api.schemas.planning_schemas import (
    MissionWeekResponse,
    PersonLoadResponse,
    PlanMemberResponse,
    PlannedMissionResponse,
    WeeklyLoadResponse,
    WorkloadPlanResponse,
)
from src.modules.planning.presentation.dependencies import get_workload_plan_use_case
from src.modules.users.domain.entities.user import User
from src.shared.utils.initials import initials

router = APIRouter(prefix="/planning", tags=["planning"])


@router.get("", response_model=WorkloadPlanResponse, operation_id="getWorkloadPlan")
async def get_workload_plan(
    horizon_months: int = Query(
        default=DEFAULT_HORIZON_MONTHS, ge=1, le=MAX_HORIZON_MONTHS
    ),
    order: list[int] = Query(default=[]),
    _: User = Depends(get_current_user),
    use_case: GetWorkloadPlanUseCase = Depends(get_workload_plan_use_case),
) -> WorkloadPlanResponse:
    """Projects the backlog onto the room the team's diaries leave.

    `order` states a hypothesis: the missions it names are served first, in
    that order, and the rest follow in the order the board already tells.
    Nothing is written — asking « et si celui-là passait devant ? » must cost
    nothing but the answer.
    """
    return to_plan_response(
        await use_case.execute(horizon_months=horizon_months, order=order)
    )


def to_plan_response(reading: WorkloadReading) -> WorkloadPlanResponse:
    return WorkloadPlanResponse(
        from_day=reading.from_day,
        to_day=reading.to_day,
        weeks=reading.weeks,
        missions=[to_mission_response(row) for row in reading.missions],
        people=[to_person_response(row) for row in reading.people],
    )


def to_mission_response(row: PlannedMissionRow) -> PlannedMissionResponse:
    return PlannedMissionResponse(
        project_id=row.mission.id or 0,
        label=row.mission.label,
        kind=row.mission.kind,
        status=row.mission.status,
        priority=row.mission.priority,
        parent_id=row.mission.parent_id,
        estimated_days=row.mission.estimated_days,
        remaining_days=row.projected.remaining_days,
        scheduled_days=row.projected.scheduled_days,
        starts_on=row.projected.starts_on,
        ends_on=row.projected.ends_on,
        target_date=row.target_date,
        slippage_days=row.slippage_days,
        blocker=row.projected.blocker,
        assignees=[to_member_response(user) for user in row.assignees],
        weeks=[
            MissionWeekResponse(week=week.week, days=week.days)
            for week in row.projected.weeks
        ],
    )


def to_person_response(row: PersonLoadRow) -> PersonLoadResponse:
    return PersonLoadResponse(
        user=to_member_response(row.user),
        weeks=[
            WeeklyLoadResponse(
                week=week.week,
                capacity=week.capacity,
                booked=week.booked,
                projected=week.projected,
                free=week.free,
                is_overloaded=week.is_overloaded,
            )
            for week in row.load.weeks
        ],
        free_days=row.load.free_days,
        first_free_week=row.load.first_free_week,
    )


def to_member_response(user: User) -> PlanMemberResponse:
    return PlanMemberResponse(
        id=user.id or 0,
        display_name=user.display_name,
        initials=initials(user.display_name),
    )
