"""The reading a projection produces: when things land, and who carries them."""

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum


class PlanBlocker(StrEnum):
    """Why a mission carries no projected date.

    Said out loud rather than dropped from the list: a mission nobody
    estimated is exactly the one steering needs to see.
    """

    #: Nobody has estimated the build, so there is no volume to place.
    NO_ESTIMATE = "no_estimate"
    #: Nobody is assigned, so there is no one to place it on.
    NO_ASSIGNEE = "no_assignee"
    #: The estimate is already spent or already forecast: nothing left to plan.
    NOTHING_LEFT = "nothing_left"
    #: What is left does not fit in the horizon looked at.
    BEYOND_HORIZON = "beyond_horizon"


@dataclass(frozen=True)
class PlannedMission:
    """A mission handed to the projection, in the order it must be served."""

    project_id: int
    #: Build left to do. None when the mission was never estimated.
    remaining_days: float | None
    #: Who may work on it. An empty tuple leaves it unplannable.
    assignees: tuple[int, ...]


@dataclass(frozen=True)
class MissionWeek:
    """Days the projection placed on a mission during one week."""

    week: date
    days: float


@dataclass(frozen=True)
class ProjectedMission:
    """What the projection has to say about one mission."""

    project_id: int
    #: What it was asked to place.
    remaining_days: float
    #: What it managed to place inside the horizon.
    scheduled_days: float
    starts_on: date | None = None
    #: The day the last remaining day lands. None when it never does.
    ends_on: date | None = None
    blocker: PlanBlocker | None = None
    weeks: list[MissionWeek] = field(default_factory=list)

    def slippage_days(self, target: date | None) -> int | None:
        """Days between the projected landing and the date the team announced.

        Positive means late. Nothing is announced when either date is missing:
        a mission with no target cannot be late, and one that does not land
        inside the horizon is not late by a measurable amount.
        """
        if target is None or self.ends_on is None:
            return None
        return (self.ends_on - target).days


@dataclass(frozen=True)
class WeeklyLoad:
    """One week of one person's diary."""

    week: date
    #: Working days that week, holidays already taken out.
    capacity: float
    #: What is already declared on them: delivered, forecast and leave alike.
    booked: float
    #: What the projection placed on top.
    projected: float

    @property
    def free(self) -> float:
        """Room the week still leaves. Never negative: an over-booked week
        offers nothing, it does not borrow from the next one."""
        return max(0.0, round(self.capacity - self.booked - self.projected, 2))

    @property
    def is_overloaded(self) -> bool:
        """More is declared than the week can hold. The grid warns, it never
        blocks: the projection reports the same way."""
        return round(self.booked + self.projected, 2) > self.capacity


@dataclass(frozen=True)
class PersonPlan:
    """A whole horizon of one person's diary, week by week."""

    user_id: int
    weeks: list[WeeklyLoad] = field(default_factory=list)

    @property
    def free_days(self) -> float:
        return round(sum(week.free for week in self.weeks), 2)

    @property
    def first_free_week(self) -> date | None:
        """The first week this person has any room at all.

        What steering asks when it wants to start something: not « is Alice
        busy », but « from when is she not »."""
        for week in self.weeks:
            if week.free > 0:
                return week.week
        return None


@dataclass(frozen=True)
class WorkloadPlan:
    """A whole projection: the missions, the people, and the weeks they span."""

    #: The weeks the horizon covers, named by their Monday, in order.
    weeks: list[date]
    missions: list[ProjectedMission]
    people: list[PersonPlan]
