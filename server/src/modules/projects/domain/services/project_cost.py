"""What a mission costs, told apart between build and run.

An estimate covers the build. Once a mission runs, what it consumes is the
price of keeping it alive, and comparing that to the build estimate would
declare every living service late. The two are therefore counted apart, and
read differently: a ratio while it is being built, a pace once it runs.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from src.modules.projects.domain.entities.project import ProjectStatus

#: Beyond this, a pace is read over the last quarter only: what a service cost
#: to keep alive two years ago says little about what it costs today.
RUN_WINDOW_DAYS = 90

#: Below this, no pace is announced. Two days spent in the first week would
#: read as eight days a month — a figure nobody measured.
MIN_RUN_DAYS_FOR_A_RATE = 30

#: A month, for turning a window of days into months. Thirty days rather than
#: the exact 30.44: the windows are whole multiples of it, which keeps the pace
#: an honest division, and one and a half percent on a steering figure changes
#: no decision.
DAYS_PER_MONTH = 30


@dataclass(frozen=True)
class ProjectCost:
    """The days a mission consumed, and what lets them be read.

    Every field but the estimate is additive, so that a parent may carry what
    its work packages cost without the reading losing its meaning.
    """

    build_days: float
    run_days: float
    #: Run consumed over the recent window, the pace is read from it.
    recent_run_days: float
    estimated_days: float | None
    #: The day the mission entered operations, if it ever did.
    in_run_since: date | None

    @property
    def has_overrun(self) -> bool:
        """Whether the build went past what was estimated for it."""
        return self.estimated_days is not None and self.build_days > self.estimated_days

    def monthly_run_rate(self, today: date) -> float | None:
        """Days per month the mission costs to keep alive.

        Nothing is announced before a month of run: the window would be too
        short for the division to mean anything.
        """
        if self.in_run_since is None:
            return None

        lived = (today - self.in_run_since).days
        if lived < MIN_RUN_DAYS_FOR_A_RATE:
            return None

        window = min(lived, RUN_WINDOW_DAYS)
        return round(self.recent_run_days / (window / DAYS_PER_MONTH), 2)

    def __add__(self, other: "ProjectCost") -> "ProjectCost":
        return ProjectCost(
            build_days=round(self.build_days + other.build_days, 2),
            run_days=round(self.run_days + other.run_days, 2),
            recent_run_days=round(self.recent_run_days + other.recent_run_days, 2),
            estimated_days=_add_estimates(self.estimated_days, other.estimated_days),
            in_run_since=_earliest(self.in_run_since, other.in_run_since),
        )


NO_COST = ProjectCost(
    build_days=0.0,
    run_days=0.0,
    recent_run_days=0.0,
    estimated_days=None,
    in_run_since=None,
)


def split_delivered(
    by_status: Mapping[ProjectStatus | None, float],
    recent_by_status: Mapping[ProjectStatus | None, float] | None = None,
    estimated_days: float | None = None,
    in_run_since: date | None = None,
) -> ProjectCost:
    """Sorts delivered days into build and run.

    Only what was declared while the mission was in operations is run. An entry
    that carries no phase counts as build: it predates the column, and a
    mission that never ran cannot have consumed run.
    """
    return ProjectCost(
        build_days=round(_sum_build(by_status), 2),
        run_days=round(by_status.get(ProjectStatus.OPERATIONS, 0.0), 2),
        recent_run_days=round(
            (recent_by_status or {}).get(ProjectStatus.OPERATIONS, 0.0), 2
        ),
        estimated_days=estimated_days,
        in_run_since=in_run_since,
    )


def roll_up(
    costs: Mapping[int, ProjectCost], parents: Mapping[int, int | None]
) -> dict[int, ProjectCost]:
    """Adds to each mission what hangs under it, however deep.

    A folded row tells what the service cost as a whole — its own build, that
    of its evolutions, and the run of all of it. Unfolded, every row reads its
    own figure again, which is why the children are left untouched here.

    The list has three levels, so a child must be added to its parent only
    once it has absorbed its own: the deepest are climbed first, and each
    carries up the total it holds by then rather than what it cost alone.
    Added in the order a mapping happens to yield, an activity would reach its
    work package after the package had already been handed to its project, and
    the days booked at the bottom would never arrive at the top.
    """
    totals = dict(costs)

    for project_id in sorted(
        parents, key=lambda pid: _depth(pid, parents), reverse=True
    ):
        parent_id = parents.get(project_id)
        if parent_id is None or parent_id not in totals:
            continue
        totals[parent_id] = totals[parent_id] + totals.get(project_id, NO_COST)

    return totals


def _depth(project_id: int, parents: Mapping[int, int | None]) -> int:
    """How many levels sit above a mission, cycles included without hanging.

    Nothing should ever write a cycle, and a reading is not the place to
    discover it: the walk simply stops on anything it has already seen.
    """
    depth = 0
    seen = {project_id}

    parent_id = parents.get(project_id)
    while parent_id is not None and parent_id not in seen:
        seen.add(parent_id)
        depth += 1
        parent_id = parents.get(parent_id)

    return depth


def _sum_build(by_status: Mapping[ProjectStatus | None, float]) -> float:
    return sum(
        days
        for status, days in by_status.items()
        if status is not ProjectStatus.OPERATIONS
    )


def _add_estimates(left: float | None, right: float | None) -> float | None:
    """A mission nobody estimated does not erase the estimate of its neighbour."""
    if left is None:
        return right
    if right is None:
        return left
    return round(left + right, 2)


def _earliest(left: date | None, right: date | None) -> date | None:
    if left is None:
        return right
    if right is None:
        return left
    return min(left, right)
