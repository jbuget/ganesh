"""What a whole projection says in one line.

Fifty-one rows say nothing at a glance. The summary is what makes a scenario
readable while one is still moving things: change the order, and the count of
late missions moves under the eye.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from src.modules.planning.domain.entities.workload_plan import (
    PersonPlan,
    PlanBlocker,
    ProjectedMission,
)

#: A day or two either side reads as on time.
#:
#: A projection is not a commitment: counting a mission late for one day would
#: make the screen cry wolf, and a plan nobody believes steers nothing. The
#: threshold lives here alone — the red mark on a row and the tally at the top
#: must never disagree.
SLIPPAGE_TOLERANCE_DAYS = 2


def is_late(landing: ProjectedMission, target: date | None) -> bool:
    """Whether a mission lands past the date the team announced."""
    slippage = landing.slippage_days(target)
    return slippage is not None and slippage > SLIPPAGE_TOLERANCE_DAYS


@dataclass(frozen=True)
class PlanSummary:
    """The state of a projection, in the few figures a decision turns on."""

    #: Missions the projection lands inside the horizon.
    planned: int
    #: Of those, the ones landing past the date announced.
    late: int
    #: Missions carrying no date at all, whatever the reason.
    blocked: int
    #: Of those, the ones blocked for want of anyone to do them. Called out on
    #: its own because it is the one the screen can do something about.
    unassigned: int
    #: Days of capacity the projection left untouched.
    free_days: float


def summarise(
    landings: Sequence[tuple[ProjectedMission, date | None]],
    people: Sequence[PersonPlan],
) -> PlanSummary:
    """Reads a whole projection into the figures a decision turns on."""
    planned = [landing for landing, _ in landings if landing.ends_on is not None]
    blocked = [landing for landing, _ in landings if landing.blocker is not None]

    return PlanSummary(
        planned=len(planned),
        late=sum(1 for landing, target in landings if is_late(landing, target)),
        blocked=len(blocked),
        unassigned=sum(
            1 for landing in blocked if landing.blocker is PlanBlocker.NO_ASSIGNEE
        ),
        free_days=round(sum(person.free_days for person in people), 2),
    )
