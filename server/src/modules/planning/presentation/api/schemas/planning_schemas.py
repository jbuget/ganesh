"""Schemas of the workload plan."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from src.modules.planning.domain.entities.roadmap import SegmentKind
from src.modules.planning.domain.entities.simulation import NAME_MAX_LENGTH
from src.modules.planning.domain.entities.workload_plan import PlanBlocker
from src.modules.planning.domain.services.horizon import (
    DEFAULT_HORIZON_MONTHS,
    MAX_HORIZON_MONTHS,
)
from src.modules.projects.domain.entities.project import (
    ProjectCategory,
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


class SaveSimulationRequest(BaseModel):
    """A scenario to write down, or to rewrite in place."""

    name: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)
    horizon_months: int = Field(ge=1, le=MAX_HORIZON_MONTHS)
    order: list[int] = Field(default_factory=list)
    staffing: dict[int, list[int]] = Field(default_factory=dict)


class SimulationResponse(BaseModel):
    """A scenario the team kept.

    It carries the hypothesis and never a result: what a scenario would cost
    depends on what has been declared since, and a landing date frozen in a row
    would be a lie by the following Monday.
    """

    id: int
    name: str
    horizon_months: int
    order: list[int]
    staffing: dict[int, list[int]]
    #: Who wrote it down. Null once that account is gone.
    author_id: int | None
    created_at: datetime
    updated_at: datetime


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


class RoadmapSegmentResponse(BaseModel):
    """One stretch of a mission's bar.

    `kind` is what keeps the screen honest: a stretch that was lived and one
    the projection supposes must never be drawn the same way, and which is
    which is decided here rather than by the colour somebody picked.
    """

    kind: SegmentKind
    status: ProjectStatus | None
    starts_on: date
    ends_on: date


class RoadmapMissionResponse(BaseModel):
    """One line of the roadmap."""

    project_id: int
    label: str
    kind: ProjectKind
    status: ProjectStatus | None
    priority: ProjectPriority | None
    #: Resolved: a work package answers with the axis of its project.
    category: ProjectCategory | None
    parent_id: int | None
    segments: list[RoadmapSegmentResponse]
    #: The date the team announced. The subject of this screen.
    target_date: date | None
    #: The day the service was recorded as going live. Null when nobody wrote
    #: it down, which is not the same as « it never did »: the bar opens its
    #: rule somewhere regardless, and that day is a placeholder.
    went_live_on: date | None
    #: Where the projection lands it. Null when it lands nowhere.
    landing_date: date | None
    #: Days between the date announced and wherever it lands — the recorded
    #: go-live when there is one, the projection otherwise. Positive means late.
    slippage_days: int | None
    is_late: bool
    estimated_days: float | None
    consumed_days: float
    remaining_days: float | None
    #: Why the projection placed nothing, when it placed nothing.
    blocker: PlanBlocker | None
    is_active: bool


class RoadmapSummaryResponse(BaseModel):
    """What a roadmap says above the bars.

    The first two are the report; the next two say how much of it to believe.
    """

    missions: int
    late: int
    undated: int
    unestimated: int
    delivered: int


class RoadmapResponse(BaseModel):
    """A whole roadmap, as the screen reads it."""

    from_day: date
    to_day: date
    #: The day the drawing was made. Where the « aujourd'hui » rule is placed,
    #: and the line between what happened and what is supposed.
    today: date
    missions: list[RoadmapMissionResponse]
    summary: RoadmapSummaryResponse
