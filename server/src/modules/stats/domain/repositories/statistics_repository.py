"""What the dashboard needs to read, expressed as a port."""

from abc import ABC, abstractmethod
from datetime import date

from src.modules.calendar.domain.entities.period import Period
from src.modules.projects.domain.entities.project import (
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)


class StatisticsRepository(ABC):
    """Aggregates read over a window.

    A read-only port: the dashboard counts, it never writes. Each method
    answers one question of the screen, so that no caller has to hold a
    thousand entries in memory to work out a percentage.
    """

    @abstractmethod
    async def declared_days(self, period: Period) -> float:
        """Person-days declared over the window, every mission together."""
        ...

    @abstractmethod
    async def contributor_ids(self, period: Period) -> set[int]:
        """Who declared at least one half day over the window."""
        ...

    @abstractmethod
    async def entry_delays(self, period: Period) -> list[int]:
        """Delay in days between the day worked and the entry that declared it.

        Read over the entries *written* during the window, not the days
        covered by it: a day worked yesterday has not yet had the chance to be
        filled in late, and counting it would flatter the figure.
        """
        ...

    @abstractmethod
    async def days_by_kind(self, period: Period) -> dict[ProjectKind, float]:
        """Declared time split between missions and what happens around them."""
        ...

    @abstractmethod
    async def days_by_status(self, period: Period) -> dict[ProjectStatus, float]:
        """Declared time per project phase, as recorded when it was entered."""
        ...

    @abstractmethod
    async def days_by_category(
        self, period: Period
    ) -> dict[ProjectCategory | None, float]:
        """Declared time per strategic axis. None covers what carries none."""
        ...

    @abstractmethod
    async def top_missions(
        self, period: Period, limit: int
    ) -> list[tuple[int, str, float]]:
        """The missions that consumed the most, as (id, label, days)."""
        ...

    @abstractmethod
    async def validated_months(self, months: list[date], user_ids: list[int]) -> int:
        """How many of these months these users have locked."""
        ...

    @abstractmethod
    async def active_missions(self) -> int:
        """Missions time can still be booked against, right now."""
        ...

    @abstractmethod
    async def active_missions_with_time(self, period: Period) -> int:
        """Active missions that received at least one half day over the window."""
        ...

    @abstractmethod
    async def missions_created(self, period: Period) -> int:
        """Missions added to the reference list during the window."""
        ...
