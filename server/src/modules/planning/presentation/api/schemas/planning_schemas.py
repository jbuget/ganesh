"""Schemas of the workload plan."""

from datetime import date

from pydantic import BaseModel, Field

from src.modules.planning.domain.entities.workload_plan import PlanBlocker
from src.modules.planning.domain.services.horizon import (
    DEFAULT_HORIZON_MONTHS,
    MAX_HORIZON_MONTHS,
)
from src.modules.projects.domain.entities.project import (
    ProjectKind,
    ProjectPriority,
    ProjectStatus,
)


class ProjectionRequest(BaseModel):
    """A scenario to project. Every field is a hypothesis, nothing is written.

    An empty body reads the plan as the team's own decisions leave it, which
    is what the screen opens on.
    """

    horizon_months: int = Field(
        default=DEFAULT_HORIZON_MONTHS, ge=1, le=MAX_HORIZON_MONTHS
    )
    #: Missions to serve first, in this order. What it leaves out follows in
    #: the order the board already tells.
    order: list[int] = Field(default_factory=list)
    #: Who to place the work on, per mission. A mission named here takes the
    #: people it names and only them; naming nobody asks what happens if it is
    #: left unstaffed. Missions absent from the map keep the team they have.
    staffing: dict[int, list[int]] = Field(default_factory=dict)


class PlanSummaryResponse(BaseModel):
    """The whole projection in the few figures a decision turns on."""

    #: Missions the projection lands inside the horizon.
    planned: int
    #: Of those, the ones landing past the date announced.
    late: int
    #: Missions carrying no date at all, whatever the reason.
    blocked: int
    #: Of those, the ones nobody is on — the blockage the screen can lift.
    unassigned: int
    #: Days of capacity the projection left untouched.
    free_days: float


class PlanMemberResponse(BaseModel):
    """Someone the work may be placed on."""

    id: int
    display_name: str
    initials: str


class MissionWeekResponse(BaseModel):
    """Days the projection placed on a mission during one week."""

    week: date
    days: float


class PlannedMissionResponse(BaseModel):
    """A mission of the backlog, and where the projection lands it."""

    project_id: int
    label: str
    kind: ProjectKind
    status: ProjectStatus | None
    priority: ProjectPriority | None
    parent_id: int | None
    estimated_days: float | None
    #: Build left to place: the estimate, less what is delivered and forecast.
    remaining_days: float
    #: What the projection managed to place inside the horizon.
    scheduled_days: float
    starts_on: date | None
    #: The day the last remaining day lands. Null when it never does.
    ends_on: date | None
    #: The date the team announced, which the landing is read against.
    target_date: date | None
    #: Days between the two. Positive means late, null when either is missing.
    slippage_days: int | None
    #: Whether it lands past the date announced, beyond what is forgiven. Read
    #: from the server so a row's mark and the tally at the top agree.
    is_late: bool
    #: Why nothing could be placed, when nothing could.
    blocker: PlanBlocker | None
    assignees: list[PlanMemberResponse]
    weeks: list[MissionWeekResponse]


class WeeklyLoadResponse(BaseModel):
    """One week of one person's diary."""

    week: date
    #: Working days that week, holidays already taken out.
    capacity: float
    #: What is already declared: delivered, forecast and leave alike.
    booked: float
    #: What the projection placed on top. A hypothesis, not a fact.
    projected: float
    #: The half day a week held back for what nobody saw coming.
    reserved: float
    #: Room left to plan on: the reserve is not part of it.
    free: float
    is_overloaded: bool


class PersonLoadResponse(BaseModel):
    """A whole horizon of one person's diary."""

    user: PlanMemberResponse
    weeks: list[WeeklyLoadResponse]
    free_days: float
    #: The first week this person has any room at all. Null when there is none.
    first_free_week: date | None


class WorkloadPlanResponse(BaseModel):
    """A whole projection, as the planning screen reads it."""

    from_day: date
    to_day: date
    #: The week columns, named by their Monday, in order.
    weeks: list[date]
    #: The backlog, in the order it was served.
    missions: list[PlannedMissionResponse]
    people: list[PersonLoadResponse]
    summary: PlanSummaryResponse
