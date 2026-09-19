"""What the interface needs to read a projection: the plan, and its names."""

from dataclasses import dataclass, field
from datetime import date

from src.modules.planning.domain.entities.workload_plan import (
    PersonPlan,
    ProjectedMission,
)
from src.modules.planning.domain.services.plan_summary import PlanSummary, is_late
from src.modules.projects.domain.entities.project import Project
from src.modules.users.domain.entities.user import User


@dataclass(frozen=True)
class PlannedMissionRow:
    """One mission of the plan, named and placed against its target."""

    mission: Project
    projected: ProjectedMission
    #: Who the projection may place the work on, in alphabetical order.
    assignees: list[User] = field(default_factory=list)

    @property
    def target_date(self) -> date | None:
        """The date the team announced, which the projection is read against."""
        return self.mission.go_live_date

    @property
    def slippage_days(self) -> int | None:
        return self.projected.slippage_days(self.target_date)

    @property
    def is_late(self) -> bool:
        """Whether it lands past the date announced, beyond what is forgiven.

        Read from the domain rather than worked out again on the screen: the
        red mark on a row and the tally at the top must never disagree.
        """
        return is_late(self.projected, self.target_date)


@dataclass(frozen=True)
class PersonLoadRow:
    """One person's diary over the horizon, named."""

    user: User
    load: PersonPlan


@dataclass(frozen=True)
class WorkloadReading:
    """A whole projection, ready to be put on screen."""

    from_day: date
    to_day: date
    #: The week columns, named by their Monday, in order.
    weeks: list[date]
    #: The backlog, in the order it was served.
    missions: list[PlannedMissionRow]
    people: list[PersonLoadRow]
    #: The whole projection in the few figures a decision turns on.
    summary: PlanSummary
