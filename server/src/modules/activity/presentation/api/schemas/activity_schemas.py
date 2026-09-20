"""Synthèse d'activité schemas.

Every rate is nullable: a window may expect nothing of anyone, and the screen
draws that differently from a zero.
"""

from datetime import date

from pydantic import BaseModel

from src.modules.calendar.domain.entities.period import PeriodRange
from src.modules.projects.domain.entities.project import (
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)


class ActivityPeriodResponse(BaseModel):
    """The window the matrix was read over."""

    range: PeriodRange
    start: date
    end: date
    working_days: int


class ContributorResponse(BaseModel):
    """Someone the window expected something of, and what they declared."""

    id: int
    display_name: str
    declared_days: float
    expected_days: float
    coverage: float | None
    #: How many missions they put time on, work packages counted apart.
    missions: int


class ActivityLineResponse(BaseModel):
    """One mission, and the days each person booked against it."""

    project_id: int
    label: str
    kind: ProjectKind
    status: ProjectStatus | None
    category: ProjectCategory | None
    #: Days per contributor id, the mission's packages counted in. Absent
    #: from the mapping is zero: the cell is simply drawn empty.
    days_by_contributor: dict[int, float]
    days: float
    #: Days on this line alone, so that an unfolded project does not show its
    #: total twice.
    own_days: float
    #: The same, per contributor: unfolded, a project's own row reads what
    #: was booked on it directly, never what its packages carry.
    own_days_by_contributor: dict[int, float]
    share: float | None
    movement: float
    is_new: bool
    packages: list["ActivityLineResponse"]


class ActivitySummaryResponse(BaseModel):
    """Everything the screen shows for one window."""

    period: ActivityPeriodResponse
    contributors: list[ContributorResponse]
    projects: list[ActivityLineResponse]
    off_project: list[ActivityLineResponse]
    project_days: float
    off_project_days: float
    declared_days: float
    expected_days: float
    coverage: float | None
