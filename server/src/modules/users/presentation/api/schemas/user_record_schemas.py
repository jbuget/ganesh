"""What the teammate panel publishes: missions, declared time, months."""

from datetime import date, datetime

from pydantic import BaseModel

from src.modules.months.domain.entities.month import MonthState
from src.modules.projects.domain.entities.project import ProjectStatus


class RecordedMissionResponse(BaseModel):
    """A mission a teammate is attached to."""

    project_id: int
    label: str
    status: ProjectStatus | None
    #: Whether they answer for the mission, beyond working on it.
    is_lead: bool


class DeclaredMissionResponse(BaseModel):
    """A mission a teammate put time on over the window."""

    project_id: int
    label: str
    days: float
    is_off_project: bool


class DeclaredWindowResponse(BaseModel):
    """What a teammate declared lately, and over which stretch."""

    since: date
    until: date
    days: float
    missions: list[DeclaredMissionResponse]


class MonthFillingResponse(BaseModel):
    """How full one month is, and whether it is closed.

    `working_days` is what the month calls for in all, `elapsed_working_days`
    what it has called for so far: a month running is read against the days
    already gone, never against the whole of it.
    """

    month: date
    delivered: float
    forecast: float
    working_days: int
    elapsed_working_days: int
    state: MonthState
    validated_at: datetime | None


class UserRecordResponse(BaseModel):
    """What the register holds on one teammate."""

    user_id: int
    missions: list[RecordedMissionResponse]
    declared: DeclaredWindowResponse
    months: list[MonthFillingResponse]
