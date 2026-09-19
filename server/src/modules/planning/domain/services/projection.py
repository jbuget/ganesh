"""Placing the backlog on the room people's diaries leave.

The rule is strict sequencing: on every day, the mission highest in the
backlog takes what its people have free before the next one is served. It is a
deliberate simplification — nobody is ever half on one thing and half on
another — and it is what makes an ordering worth arbitrating: move a mission
up, and one sees exactly who lands later for it.

The function is pure. It reads no clock and no database: the days it may fill
and what is already booked on them are handed in, which is what lets a
what-if be run on a hypothetical order without writing anything down.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta

from src.modules.planning.domain.entities.capacity import EPSILON, Capacity
from src.modules.planning.domain.entities.workload_plan import (
    MissionWeek,
    PersonPlan,
    PlanBlocker,
    PlannedMission,
    ProjectedMission,
    WeeklyLoad,
    WorkloadPlan,
)


def week_of(day: date) -> date:
    """The Monday of the week a day belongs to."""
    return day - timedelta(days=day.weekday())


def project_workload(
    backlog: Sequence[PlannedMission],
    days: Sequence[date],
    booked: Mapping[int, Mapping[date, float]],
    user_ids: Sequence[int],
) -> WorkloadPlan:
    """Lands the backlog, in the order given, on the days given.

    `backlog` is already ordered: arbitrating the order is the caller's
    business, and running the same backlog through twice in two orders is
    exactly how a what-if is answered.
    """
    window = list(days)
    weeks = _weeks_of(window)
    capacity = Capacity.over(user_ids, window, booked)

    runs = [_Run(mission) for mission in backlog]
    plannable = [run for run in runs if run.blocker is None]

    for day in window:
        for run in plannable:
            if run.ends_on is not None:
                continue
            for user_id in run.mission.assignees:
                if run.left <= EPSILON:
                    break
                taken = capacity.take(user_id, day, run.left)
                if taken > 0.0:
                    run.place(user_id, day, taken)
            if run.left <= EPSILON:
                run.ends_on = day

    return WorkloadPlan(
        weeks=weeks,
        missions=[run.landed() for run in runs],
        people=[
            _person_plan(user_id, weeks, window, booked, runs) for user_id in user_ids
        ],
    )


@dataclass
class _Run:
    """One mission being placed, and what the placing leaves behind."""

    mission: PlannedMission
    left: float = 0.0
    starts_on: date | None = None
    ends_on: date | None = None
    blocker: PlanBlocker | None = None
    #: Days placed, per week.
    by_week: dict[date, float] = field(default_factory=dict)
    #: Days placed, per person and per week: the other way to read the same
    #: placing, and what fills a person's diary.
    by_person_week: dict[tuple[int, date], float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.blocker = _cannot_be_planned(self.mission)
        self.left = self.mission.remaining_days or 0.0

    def place(self, user_id: int, day: date, days: float) -> None:
        week = week_of(day)
        self.left -= days
        self.by_week[week] = self.by_week.get(week, 0.0) + days
        key = (user_id, week)
        self.by_person_week[key] = self.by_person_week.get(key, 0.0) + days
        if self.starts_on is None:
            self.starts_on = day

    @property
    def placed(self) -> float:
        return sum(self.by_week.values())

    def landed(self) -> ProjectedMission:
        """What the projection has to say about this mission once it is done."""
        # A mission that ran out of horizon is not a mission nobody could plan:
        # the first reason found stands, and the horizon only speaks last.
        blocker = self.blocker
        if blocker is None and self.ends_on is None:
            blocker = PlanBlocker.BEYOND_HORIZON

        return ProjectedMission(
            project_id=self.mission.project_id,
            remaining_days=round(self.mission.remaining_days or 0.0, 2),
            scheduled_days=round(self.placed, 2),
            starts_on=self.starts_on,
            ends_on=self.ends_on,
            blocker=blocker,
            weeks=[
                MissionWeek(week=week, days=round(days, 2))
                for week, days in sorted(self.by_week.items())
            ],
        )


def _cannot_be_planned(mission: PlannedMission) -> PlanBlocker | None:
    """Why this mission cannot be placed at all, if it cannot.

    Order matters: a mission nobody estimated is first of all unestimated,
    whether or not anyone is assigned to it.
    """
    if mission.remaining_days is None:
        return PlanBlocker.NO_ESTIMATE
    if mission.remaining_days <= EPSILON:
        return PlanBlocker.NOTHING_LEFT
    if not mission.assignees:
        return PlanBlocker.NO_ASSIGNEE
    return None


def _weeks_of(window: Sequence[date]) -> list[date]:
    """The weeks the window spans, named by their Monday, in order."""
    return sorted({week_of(day) for day in window})


def _person_plan(
    user_id: int,
    weeks: Sequence[date],
    window: Sequence[date],
    booked: Mapping[int, Mapping[date, float]],
    runs: Sequence[_Run],
) -> PersonPlan:
    """One person's diary over the horizon, week by week.

    What is already declared stays told apart from what the projection added:
    the first is a fact, the second a hypothesis, and steering must never read
    one for the other.
    """
    diary = booked.get(user_id, {})

    capacity: dict[date, float] = {}
    declared: dict[date, float] = {}
    for day in window:
        week = week_of(day)
        capacity[week] = capacity.get(week, 0.0) + 1.0
        declared[week] = declared.get(week, 0.0) + diary.get(day, 0.0)

    projected: dict[date, float] = {}
    for run in runs:
        for (placed_on, week), days in run.by_person_week.items():
            if placed_on == user_id:
                projected[week] = projected.get(week, 0.0) + days

    return PersonPlan(
        user_id=user_id,
        weeks=[
            WeeklyLoad(
                week=week,
                capacity=round(capacity.get(week, 0.0), 2),
                booked=round(declared.get(week, 0.0), 2),
                projected=round(projected.get(week, 0.0), 2),
            )
            for week in weeks
        ],
    )
