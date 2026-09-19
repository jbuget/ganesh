"""Schemas of the workload plan."""

from datetime import date

from pydantic import BaseModel

from src.modules.planning.domain.entities.workload_plan import PlanBlocker
from src.modules.projects.domain.entities.project import (
    ProjectKind,
    ProjectPriority,
    ProjectStatus,
)


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
