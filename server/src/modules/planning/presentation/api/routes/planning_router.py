"""Routes of the workload plan.

The plan is read by the whole team, as the board is: knowing what is coming
and who is taken is everybody's business. Only what writes stays a manager's
privilege, and a projection writes nothing.
"""

from datetime import date

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.planning.application.dtos.workload_dto import (
    PersonLoadRow,
    PlannedMissionRow,
    WorkloadReading,
)
from src.modules.planning.application.use_cases.get_roadmap import GetRoadmapUseCase
from src.modules.planning.application.use_cases.get_workload_plan import (
    GetWorkloadPlanUseCase,
)
from src.modules.planning.application.use_cases.manage_simulations import (
    DeleteSimulationUseCase,
    ListSimulationsUseCase,
    SaveSimulationUseCase,
    SimulationCommand,
    UpdateSimulationUseCase,
)
from src.modules.planning.domain.entities.roadmap import Roadmap, RoadmapMission
from src.modules.planning.domain.entities.simulation import Simulation
from src.modules.planning.presentation.api.schemas.planning_schemas import (
    MissionWeekResponse,
    PersonLoadResponse,
    PlanMemberResponse,
    PlannedMissionResponse,
    PlanSummaryResponse,
    ProjectionRequest,
    RoadmapMissionResponse,
    RoadmapResponse,
    RoadmapSegmentResponse,
    RoadmapSummaryResponse,
    SaveSimulationRequest,
    SimulationResponse,
    WeeklyLoadResponse,
    WorkloadPlanResponse,
)
from src.modules.planning.presentation.dependencies import (
    get_delete_simulation_use_case,
    get_list_simulations_use_case,
    get_roadmap_use_case,
    get_save_simulation_use_case,
    get_update_simulation_use_case,
    get_workload_plan_use_case,
)
from src.modules.users.domain.entities.user import User
from src.shared.utils.initials import initials

router = APIRouter(prefix="/planning", tags=["planning"])


@router.post(
    "/projection",
    response_model=WorkloadPlanResponse,
    operation_id="projectWorkload",
)
async def project_workload(
    scenario: ProjectionRequest | None = None,
    _: User = Depends(get_current_user),
    use_case: GetWorkloadPlanUseCase = Depends(get_workload_plan_use_case),
) -> WorkloadPlanResponse:
    """Projects the backlog onto the room the team's diaries leave.

    A POST that writes nothing: the body carries a scenario — an order to
    serve, people to place the work on — and the answer is what that scenario
    would cost. Asking « et si celui-là passait devant, avec Valentin dessus ? »
    must leave the board exactly as it was.

    It is a POST and not a GET because a scenario is a structure, not a string:
    squeezing a map of missions to people through a query string would mean
    inventing an encoding, and hand-writing the type that reads it back.
    """
    asked = scenario or ProjectionRequest()
    return to_plan_response(
        await use_case.execute(
            horizon_months=asked.horizon_months,
            order=asked.order,
            staffing=asked.staffing,
        )
    )


def to_plan_response(reading: WorkloadReading) -> WorkloadPlanResponse:
    return WorkloadPlanResponse(
        from_day=reading.from_day,
        to_day=reading.to_day,
        weeks=reading.weeks,
        missions=[to_mission_response(row) for row in reading.missions],
        people=[to_person_response(row) for row in reading.people],
        summary=PlanSummaryResponse(
            planned=reading.summary.planned,
            late=reading.summary.late,
            blocked=reading.summary.blocked,
            unassigned=reading.summary.unassigned,
            free_days=reading.summary.free_days,
        ),
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
        is_late=row.is_late,
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
                reserved=week.reserved,
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
        display_name=user.label,
        initials=initials(user.label),
    )


@router.get(
    "/roadmap",
    response_model=RoadmapResponse,
    operation_id="readRoadmap",
)
async def read_roadmap(
    from_day: date | None = None,
    to_day: date | None = None,
    _: User = Depends(get_current_user),
    use_case: GetRoadmapUseCase = Depends(get_roadmap_use_case),
) -> RoadmapResponse:
    """The portfolio over a window of time: what was delivered, what is promised.

    A GET, where the projection is a POST: a window is two dates, and two
    dates go in a query string without anyone having to invent an encoding.
    Leaving them out reads the civil year, which is what the screen opens on.
    """
    return to_roadmap_response(await use_case.execute(from_day=from_day, to_day=to_day))


def to_roadmap_response(roadmap: Roadmap) -> RoadmapResponse:
    return RoadmapResponse(
        from_day=roadmap.from_day,
        to_day=roadmap.to_day,
        today=roadmap.today,
        missions=[to_roadmap_mission_response(line) for line in roadmap.missions],
        summary=RoadmapSummaryResponse(
            missions=roadmap.summary.missions,
            late=roadmap.summary.late,
            undated=roadmap.summary.undated,
            unestimated=roadmap.summary.unestimated,
            delivered=roadmap.summary.delivered,
        ),
    )


def to_roadmap_mission_response(line: RoadmapMission) -> RoadmapMissionResponse:
    return RoadmapMissionResponse(
        project_id=line.project_id,
        label=line.label,
        kind=line.kind,
        status=line.status,
        priority=line.priority,
        category=line.category,
        parent_id=line.parent_id,
        segments=[
            RoadmapSegmentResponse(
                kind=segment.kind,
                status=segment.status,
                starts_on=segment.starts_on,
                ends_on=segment.ends_on,
            )
            for segment in line.segments
        ],
        target_date=line.target_date,
        landing_date=line.landing_date,
        slippage_days=line.slippage_days,
        is_late=line.is_late,
        estimated_days=line.estimated_days,
        consumed_days=line.consumed_days,
        remaining_days=line.remaining_days,
        blocker=line.blocker,
        is_active=line.is_active,
    )


@router.get(
    "/simulations",
    response_model=list[SimulationResponse],
    operation_id="listSimulations",
)
async def list_simulations(
    _: User = Depends(get_current_user),
    use_case: ListSimulationsUseCase = Depends(get_list_simulations_use_case),
) -> list[SimulationResponse]:
    """The scenarios the team kept, most recently touched first.

    Whole, not as a list of names: each holds a handful of numbers, and
    picking one must not cost a round trip before the plan can be redrawn.
    """
    return [to_simulation_response(s) for s in await use_case.execute()]


@router.post(
    "/simulations",
    response_model=SimulationResponse,
    status_code=201,
    operation_id="saveSimulation",
)
async def save_simulation(
    body: SaveSimulationRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    use_case: SaveSimulationUseCase = Depends(get_save_simulation_use_case),
) -> SimulationResponse:
    """Writes a scenario down, under a name nobody else is using."""
    assert current_user.id is not None
    saved = await use_case.execute(to_command(body), author_id=current_user.id)
    await session.commit()
    return to_simulation_response(saved)


@router.put(
    "/simulations/{simulation_id}",
    response_model=SimulationResponse,
    operation_id="updateSimulation",
)
async def update_simulation(
    simulation_id: int,
    body: SaveSimulationRequest,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    use_case: UpdateSimulationUseCase = Depends(get_update_simulation_use_case),
) -> SimulationResponse:
    """Rewrites a scenario in place, so trying again costs no second row."""
    rewritten = await use_case.execute(simulation_id, to_command(body))
    await session.commit()
    return to_simulation_response(rewritten)


@router.delete(
    "/simulations/{simulation_id}",
    status_code=204,
    operation_id="deleteSimulation",
)
async def delete_simulation(
    simulation_id: int,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    use_case: DeleteSimulationUseCase = Depends(get_delete_simulation_use_case),
) -> Response:
    """Drops a scenario.

    Anyone may, whoever wrote it: a simulation holds no declared time and
    changes nothing that was decided. Trust is the stance here as on the board.
    """
    await use_case.execute(simulation_id)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def to_command(body: SaveSimulationRequest) -> SimulationCommand:
    return SimulationCommand(
        name=body.name,
        horizon_months=body.horizon_months,
        order=body.order,
        staffing=body.staffing,
    )


def to_simulation_response(simulation: Simulation) -> SimulationResponse:
    assert simulation.id is not None
    assert simulation.created_at is not None and simulation.updated_at is not None
    return SimulationResponse(
        id=simulation.id,
        name=simulation.name,
        horizon_months=simulation.horizon_months,
        order=simulation.order,
        staffing=simulation.staffing,
        author_id=simulation.author_id,
        created_at=simulation.created_at,
        updated_at=simulation.updated_at,
    )
