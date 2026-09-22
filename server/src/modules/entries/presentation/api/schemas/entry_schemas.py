"""Input and output schemas for entries."""

from datetime import date

from pydantic import BaseModel, Field

from src.modules.projects.domain.entities.project import ProjectKind, ProjectStatus


class SetEntryRequest(BaseModel):
    """Request to write an entry."""

    project_id: int
    day: date
    value: float = Field(description="0.5 for a half day, 1 for a full day")


class AddMissionRequest(BaseModel):
    """Request to put a mission on a month, before any time is entered on it."""

    project_id: int
    month: date = Field(description="Any day of the month aimed at")


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
    #: What the month calls for from this person, their rhythm honoured.
    expected_days: float
    is_writable: bool
    actual_total: float
    forecast_total: float


class ExportedEntryResponse(BaseModel):
    """One declared day, as an export hands it over.

    Ids and labels together: the labels make the row readable on its own, the
    ids make two pulls reconcilable.
    """

    day: date
    value: float
    status_at_entry: ProjectStatus | None
    user_id: int
    user_label: str
    project_id: int
    project_label: str


class EntriesExportResponse(BaseModel):
    """Everything declared over a window, and the window it was read over."""

    from_day: date
    to_day: date
    entries: list[ExportedEntryResponse]
