"""The figures the dashboard reads, and the rules behind them.

Every rate here can be unknown. A period may expect nothing of anyone — a
weekend, a team with nobody in it, a window closing no month — and in that
case a zero would read as a failure that is not one. `None` says "there is
nothing to read", which is a different statement, and the screen draws it
differently.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from statistics import median

from src.modules.calendar.domain.entities.period import Period
from src.modules.projects.domain.entities.project import ProjectCategory, ProjectStatus
from src.modules.stats.domain.entities.surface_usage import SurfaceUsage

#: Up to this delay, an entry was still written from memory of the day itself.
DAY_TO_DAY_DELAY = 2

#: Beyond this, the day is reconstructed rather than remembered: whatever is
#: declared then says more about the calendar than about the work.
LATE_DELAY = 15


def _rate(part: float, whole: float) -> float | None:
    """Share of `part` in `whole`, or None when there is nothing to divide."""
    return None if whole == 0 else part / whole


@dataclass(frozen=True)
class Coverage:
    """How much of the expected time was actually declared.

    The lead figure: it measures adoption and conditions everything else at
    once. Read against a coverage of 60 %, every report drawn from Timesheet
    is a costly fiction.
    """

    declared_days: float
    expected_days: float

    @property
    def rate(self) -> float | None:
        return _rate(self.declared_days, self.expected_days)

    @property
    def missing_days(self) -> float:
        """Person-days still to declare. An excess leaves nothing missing."""
        return max(0.0, self.expected_days - self.declared_days)

    def delta_in_points(self, previous: "Coverage") -> float | None:
        """Movement against the previous window, in percentage points."""
        if self.rate is None or previous.rate is None:
            return None
        return (self.rate - previous.rate) * 100


@dataclass(frozen=True)
class Freshness:
    """How long days waited between being worked and being declared.

    The guard rail that keeps coverage honest: without it, the rate climbs
    just as well on a month-end catch-up reconstructed from memory.

    The median, not the average: one day caught up four months late must not
    drag the whole reading with it.
    """

    #: Delay in days between the day worked and the moment it was entered.
    delays: list[int] = field(default_factory=list)

    @property
    def entries(self) -> int:
        return len(self.delays)

    @property
    def median_delay(self) -> float | None:
        return None if not self.delays else float(median(self.delays))

    @property
    def day_to_day_share(self) -> float | None:
        """Share of entries written while the day was still fresh."""
        return self._share_of(lambda delay: delay <= DAY_TO_DAY_DELAY)

    @property
    def late_share(self) -> float | None:
        """Share of entries caught up long after the fact."""
        return self._share_of(lambda delay: delay > LATE_DELAY)

    def _share_of(self, matches: Callable[[int], bool]) -> float | None:
        return _rate(sum(1 for delay in self.delays if matches(delay)), self.entries)


@dataclass(frozen=True)
class Teammate:
    """Someone on the team, named."""

    id: int
    display_name: str


@dataclass(frozen=True)
class Adoption:
    """How much of the team took part over the window.

    Naming those who declared nothing is deliberate: the figure is read by
    everyone, and a coverage rate only moves when someone knows it is theirs
    to move.
    """

    contributors: int
    idle: list[Teammate] = field(default_factory=list)

    @property
    def expected_contributors(self) -> int:
        return self.contributors + len(self.idle)

    @property
    def rate(self) -> float | None:
        return _rate(self.contributors, self.expected_contributors)


@dataclass(frozen=True)
class MonthValidation:
    """Whether the months the window closed were locked.

    Only closed months count: a month still running is not late, it is simply
    not over.
    """

    validated: int
    due: int

    @property
    def rate(self) -> float | None:
        return _rate(self.validated, self.due)


@dataclass(frozen=True)
class MissionShare:
    """Time booked against one mission, and its weight in the window."""

    project_id: int
    label: str
    days: float
    total_days: float

    @property
    def share(self) -> float | None:
        return _rate(self.days, self.total_days)


@dataclass(frozen=True)
class Steering:
    """Where the declared time went.

    The floor that proves the point: time per phase and per strategic axis is
    what the entries were captured for in the first place.
    """

    project_days: float
    off_project_days: float
    by_status: dict[ProjectStatus, float] = field(default_factory=dict)
    by_category: dict[ProjectCategory | None, float] = field(default_factory=dict)
    top_missions: list[MissionShare] = field(default_factory=list)

    @property
    def total_days(self) -> float:
        return self.project_days + self.off_project_days

    @property
    def project_share(self) -> float | None:
        """Share of the time that went to a mission rather than around it."""
        return self.share_of(self.project_days)

    def share_of(self, days: float) -> float | None:
        """Weight of a slice of the declared time in the whole window.

        Every breakdown reads its weight from here: a phase, an axis and a
        mission all answer the same question, and the answer is a domain rule
        rather than something each screen works out for itself.
        """
        return _rate(days, self.total_days)


@dataclass(frozen=True)
class Registry:
    """Whether the mission reference list still matches the real work."""

    active_missions: int
    missions_with_time: int
    created: int

    @property
    def missions_without_time(self) -> int:
        """Active missions nobody booked a single half day against."""
        return max(0, self.active_missions - self.missions_with_time)

    @property
    def usage_rate(self) -> float | None:
        return _rate(self.missions_with_time, self.active_missions)


@dataclass(frozen=True)
class Statistics:
    """Everything the dashboard shows for one window.

    The lead figure comes with the one before it: a coverage rate says little
    on its own, and much once it is read as moving.
    """

    period: Period
    coverage: Coverage
    previous_coverage: Coverage
    freshness: Freshness
    month_validation: MonthValidation
    adoption: Adoption
    surfaces: SurfaceUsage
    steering: Steering
    registry: Registry

    @property
    def coverage_delta_in_points(self) -> float | None:
        return self.coverage.delta_in_points(self.previous_coverage)
