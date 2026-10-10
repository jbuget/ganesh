"""What the dashboard needs to read, expressed as a port."""

from abc import ABC, abstractmethod
from datetime import date

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.calendar.domain.entities.period import Period
from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.projects.domain.entities.project import (
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.requests.domain.entities.request import RequestState
from src.modules.stats.domain.entities.surface_usage import Surface, Tally, Trace
from src.shared.enums.work_nature import WorkNature


class StatisticsRepository(ABC):
    """Aggregates read over a window.

    A read-only port: the dashboard counts, it never writes. Each method
    answers one question of the screen, so that no caller has to hold a
    thousand entries in memory to work out a percentage.
    """

    @abstractmethod
    async def declared_days(self, period: Period, user_ids: list[int]) -> float:
        """Person-days these users declared over the window, every mission
        together."""
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
    async def days_by_nature(self, period: Period) -> dict[WorkNature | None, float]:
        """Declared project time per trade. None covers what states none.

        Off-project work is left out: an absence is booked against itself and
        has no trade to be read under.
        """
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

    @abstractmethod
    async def missions_without_activity(self) -> int:
        """Active missions nothing can be declared on, for want of a trade.

        Off-project work is booked against directly, and a project cut into
        work packages is declared on through them: neither is asked for one.
        """
        ...

    @abstractmethod
    async def missions_unbudgeted(self) -> int:
        """Active missions cut into trades, at least one left unbudgeted."""
        ...

    @abstractmethod
    async def followed_missions(self) -> int:
        """Active missions the team keeps an eye on."""
        ...

    @abstractmethod
    async def published_missions(self) -> int:
        """Active missions published to the catalogue."""
        ...

    @abstractmethod
    async def requests_submitted(self, period: Period) -> int:
        """Needs handed over to be weighed during the window."""
        ...

    @abstractmethod
    async def requests_decided(self, period: Period) -> dict[RequestState, int]:
        """Needs weighed during the window, by the state they are in now."""
        ...

    @abstractmethod
    async def requests_converted(self, period: Period) -> int:
        """Needs that became a mission during the window."""
        ...

    @abstractmethod
    async def requests_waiting_since(self) -> list[date]:
        """The day each need still waiting for an answer was handed over."""
        ...

    @abstractmethod
    async def active_projects(self) -> int:
        """Active projects proper: not work packages, not off-project work."""
        ...

    @abstractmethod
    async def projects_without_role(self, role: ProjectRole) -> int:
        """Active projects nobody is attached to under this role."""
        ...

    @abstractmethod
    async def followed_last_news(self) -> list[date | None]:
        """For each followed active project, the day of its latest update.

        None where none was ever posted. A withdrawn update is not news: its
        words are gone.
        """
        ...

    @abstractmethod
    async def updates_posted(self, period: Period) -> int:
        """Updates posted during the window, withdrawn ones left out."""
        ...

    @abstractmethod
    async def updates_answered(self, period: Period) -> int:
        """Of those, the ones somebody other than the author answered.

        A reply or a reaction both count: answering without writing is the
        cheapest thing one can say, and it is still an answer.
        """
        ...

    @abstractmethod
    async def notification_reading(
        self, period: Period
    ) -> dict[NotificationKind, tuple[int, int]]:
        """Per kind, notifications written during the window and opened ones."""
        ...

    @abstractmethod
    async def unread_notifications(self, older_than: date | None = None) -> int:
        """Notifications still waiting, optionally only those written before a day."""
        ...

    @abstractmethod
    async def surface_traces(self, period: Period) -> list[Trace]:
        """Gestures of the window, one line per action and per person.

        Grouped rather than listed, and left unfolded: which function a
        gesture belongs to is business knowledge, and it stays in the domain
        rather than turning into a `CASE` in the SQL.
        """
        ...

    @abstractmethod
    async def unlogged_tallies(self, period: Period) -> dict[Surface, Tally]:
        """What the functions the audit log does not carry saw."""
        ...

    @abstractmethod
    async def last_gestures(self) -> dict[AuditAction, date]:
        """The day each gesture was last made, however far back that is.

        Read beyond any window on purpose: it is what tells a function nobody
        used this month from one nobody has used since March.
        """
        ...

    @abstractmethod
    async def last_unlogged_use(self) -> dict[Surface, date]:
        """The same, for the functions counted outside the log."""
        ...
