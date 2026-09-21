"""Dashboard schemas.

Every rate is nullable: a window may expect nothing of anyone, and the screen
draws that differently from a zero.
"""

from datetime import date

from pydantic import BaseModel

from src.modules.calendar.domain.entities.period import PeriodRange
from src.modules.projects.domain.entities.project import ProjectCategory, ProjectStatus
from src.modules.stats.domain.entities.surface_usage import Surface


class PeriodResponse(BaseModel):
    """The window the figures were read over."""

    range: PeriodRange
    start: date
    end: date
    working_days: int


class CoverageResponse(BaseModel):
    """How much of the expected time was declared."""

    declared_days: float
    expected_days: float
    missing_days: float
    rate: float | None
    delta_in_points: float | None


class FreshnessResponse(BaseModel):
    """How long days waited before being declared."""

    entries: int
    median_delay: float | None
    day_to_day_share: float | None
    late_share: float | None


class MonthValidationResponse(BaseModel):
    """Closed months, and those that were locked."""

    validated: int
    due: int
    rate: float | None


class TeammateResponse(BaseModel):
    id: int
    display_name: str


class AdoptionResponse(BaseModel):
    """How much of the team took part."""

    contributors: int
    expected_contributors: int
    rate: float | None
    idle: list[TeammateResponse]


class SurfaceActivityResponse(BaseModel):
    """What one function of the product saw over the window."""

    surface: Surface
    people: int
    gestures: int
    #: Movement in people, never in gestures: one tidy-up afternoon doubles
    #: the second, while somebody who came or stopped coming is adoption.
    delta_in_people: int
    #: Read beyond the window, and null when nobody has ever used it.
    last_used_on: date | None


class SurfaceUsageResponse(BaseModel):
    """What the product saw, function by function, in a fixed order."""

    activities: list[SurfaceActivityResponse]
    idle_count: int


class StatusShareResponse(BaseModel):
    """Time booked in one project phase."""

    status: ProjectStatus
    days: float
    share: float | None


class CategoryShareResponse(BaseModel):
    """Time booked on one strategic axis. A null axis carries none."""

    category: ProjectCategory | None
    days: float
    share: float | None


class MissionShareResponse(BaseModel):
    """Time booked against one mission."""

    project_id: int
    label: str
    days: float
    share: float | None


class SteeringResponse(BaseModel):
    """Where the declared time went."""

    project_days: float
    off_project_days: float
    project_share: float | None
    by_status: list[StatusShareResponse]
    by_category: list[CategoryShareResponse]
    top_missions: list[MissionShareResponse]


class RegistryResponse(BaseModel):
    """Whether the mission reference list still matches the real work."""

    active_missions: int
    missions_with_time: int
    missions_without_time: int
    usage_rate: float | None
    created: int


class StatisticsResponse(BaseModel):
    """Everything the dashboard shows for one window."""

    period: PeriodResponse
    coverage: CoverageResponse
    freshness: FreshnessResponse
    month_validation: MonthValidationResponse
    adoption: AdoptionResponse
    surfaces: SurfaceUsageResponse
    steering: SteeringResponse
    registry: RegistryResponse
