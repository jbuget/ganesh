"""What the Synthèse d'activité needs to read, expressed as a port."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.modules.calendar.domain.entities.period import Period
from src.modules.projects.domain.entities.project import (
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)


@dataclass(frozen=True)
class DeclaredDays:
    """Days one person booked on one mission over a window."""

    project_id: int
    user_id: int
    days: float


@dataclass(frozen=True)
class MissionRecord:
    """A mission the window touched, as the reference list holds it."""

    project_id: int
    label: str
    kind: ProjectKind
    status: ProjectStatus | None
    category: ProjectCategory | None
    parent_id: int | None


class ActivityRepository(ABC):
    """Aggregates read over a window.

    A read-only port: the screen counts, it never writes. Each method answers
    one question, so that no caller has to hold thousands of entries in
    memory to work out a matrix.
    """

    @abstractmethod
    async def declared_days(self, period: Period) -> list[DeclaredDays]:
        """One row per person and per mission, days already added up.

        A single grouped read, never one query per mission: the matrix is a
        `GROUP BY` and nothing more.
        """
        ...

    @abstractmethod
    async def missions_touched(self, period: Period) -> list[MissionRecord]:
        """The missions that received time, **and their parents**.

        The parents matter even when they received nothing themselves: a work
        package rolls up into its project, and a project with no label to
        roll into would leave the package stranded at the top level.
        """
        ...

    @abstractmethod
    async def days_by_mission(self, period: Period) -> dict[int, float]:
        """Days per mission, every person together.

        Read over the window before the one on screen, to say what moved.
        """
        ...
