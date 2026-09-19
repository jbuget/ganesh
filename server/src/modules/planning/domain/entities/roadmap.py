"""What a roadmap draws: one bar per mission, told in segments.

The planning screen answers « qu'est-ce qui rentre, et qui le porte ». This one
answers « qu'est-ce qu'on livre, et quand », which is a different question and
a different reader: the plan is arbitrated by the team, the roadmap is shown
outside it.

Hence the one distinction the whole reading rests on. A segment is either
something that happened, something the projection supposes, or a service that
runs and does not end. Reading a supposition as a commitment is the mistake
this screen exists to prevent, so the three are named apart here rather than
told apart by a colour someone chose on the front end.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum

from src.modules.planning.domain.entities.workload_plan import PlanBlocker
from src.modules.projects.domain.entities.project import (
    ProjectCategory,
    ProjectKind,
    ProjectPriority,
    ProjectStatus,
)


class SegmentKind(StrEnum):
    """What a stretch of a bar is made of."""

    #: Constaté: time has been declared, phases have been crossed. A fact.
    LIVED = "lived"
    #: What the projection supposes, and nothing more.
    PROJECTED = "projected"
    #: A service being kept alive. It has no end, which is the point of it.
    RUNNING = "running"


@dataclass(frozen=True)
class RoadmapSegment:
    """One stretch of one mission's bar.

    Both ends are inclusive days. A segment of a single day is legitimate: a
    phase crossed and left the same afternoon still happened.
    """

    kind: SegmentKind
    #: The phase it was spent in, which is what gives it its colour. None when
    #: the mission carries no phase — off-project work never reaches here.
    status: ProjectStatus | None
    starts_on: date
    ends_on: date

    def overlaps(self, start: date, end: date) -> bool:
        return self.starts_on <= end and self.ends_on >= start


@dataclass(frozen=True)
class RoadmapMission:
    """One line of the roadmap: a mission, its bar, and what it promised."""

    project_id: int
    label: str
    kind: ProjectKind
    status: ProjectStatus | None
    priority: ProjectPriority | None
    #: Resolved: a work package answers with the axis of its project, so that
    #: grouping by axis never drops it into a band of its own.
    category: ProjectCategory | None
    parent_id: int | None
    segments: list[RoadmapSegment] = field(default_factory=list)
    #: The date the team announced. The subject of this screen, where the plan
    #: only ever reads it to work out a delay.
    target_date: date | None = None
    #: Where the projection lands it. None when it lands nowhere.
    landing_date: date | None = None
    #: Days between the two. Positive means late.
    slippage_days: int | None = None
    #: Past what is forgiven. Read from the domain so that a red bar and the
    #: tally above it can never disagree.
    is_late: bool = False
    estimated_days: float | None = None
    consumed_days: float = 0.0
    remaining_days: float | None = None
    #: Why the projection placed nothing, when it placed nothing. Said out
    #: loud: a mission with no bar is a question, not an absence.
    blocker: PlanBlocker | None = None
    #: Whether the mission is still on the reference list.
    is_active: bool = True

    @property
    def is_running(self) -> bool:
        return self.status is ProjectStatus.OPERATIONS

    @property
    def is_awaited(self) -> bool:
        """Still on the list, and not yet delivered: something is owed here."""
        return self.is_active and not self.is_running

    @property
    def has_bar(self) -> bool:
        return bool(self.segments)

    def shows_between(self, start: date, end: date, today: date) -> bool:
        """Whether this line has anything to say inside a window.

        Three ways of having something to say. The bar reaches into the
        window; or the date announced falls in it; or the mission is still
        owed and the window looks ahead — a mission nobody estimated and
        nobody dated draws nothing at all, and is exactly the line steering
        has to see. Only a window entirely in the past leaves it out: what was
        owed last year is not what last year delivered.
        """
        if any(segment.overlaps(start, end) for segment in self.segments):
            return True
        if self.target_date is not None and start <= self.target_date <= end:
            return True
        return self.is_awaited and end >= today


@dataclass(frozen=True)
class RoadmapSummary:
    """The state of a roadmap, in the figures a reader takes away from it."""

    #: Lines drawn, whatever they carry.
    missions: int
    #: Landing past the date announced.
    late: int
    #: Still to build, and never given a date.
    undated: int
    #: Still to build, and never estimated: they carry no projected end.
    unestimated: int
    #: Missions that entered operations inside the window. What went out.
    delivered: int


@dataclass(frozen=True)
class Roadmap:
    """A whole roadmap: the window it covers, and the lines in it."""

    from_day: date
    to_day: date
    today: date
    missions: list[RoadmapMission]
    summary: RoadmapSummary
