"""Input and output schemas for entries."""

from datetime import date

from pydantic import BaseModel, Field

from src.modules.projects.domain.entities.project import ProjectKind


class SetEntryRequest(BaseModel):
    """Request to write an entry."""

    project_id: int
    day: date
    value: float = Field(description="0.5 for a half day, 1 for a full day")


class EntryResponse(BaseModel):
    """A recorded entry."""

    project_id: int
    day: date
    value: float


class CalendarDayResponse(BaseModel):
    """A day of the month and its kind."""

    day: date
    kind: str
    label: str | None = None
    is_off_day: bool


class GridRowResponse(BaseModel):
    """One grid row: a mission and its entries."""

    project_id: int
    label: str
    kind: ProjectKind
    estimated_days: float | None
    values: dict[date, float]
    actual_total: float
    forecast_total: float
    total: float
    total_consumed_days: float


class DayTotalResponse(BaseModel):
    """Total entered on one day."""

    day: date
    total: float
    exceeds_capacity: bool


class MonthGridResponse(BaseModel):
    """The complete grid for a month."""

    user_id: int
    month: date
    days: list[CalendarDayResponse]
    rows: list[GridRowResponse]
    day_totals: list[DayTotalResponse]
    working_days: int
    is_writable: bool
    actual_total: float
    forecast_total: float
