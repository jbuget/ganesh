"""The matrix the Synthèse d'activité reads: who did what, and on what.

Rétrospective and factual, where Planification is prospective and arbitrated:
nothing here is placed or supposed, everything was declared. The screen that
reads it is the one a manager opens to ask where the time went, and the
figures only mean something once the coverage above them is known — a matrix
read against a coverage of 60 % is a costly fiction, exactly as on the
Statistiques screen.
"""

from dataclasses import dataclass, field

from src.modules.calendar.domain.entities.period import Period
from src.modules.projects.domain.entities.project import (
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)


def _rate(part: float, whole: float) -> float | None:
    """Share of `part` in `whole`, or None when there is nothing to divide."""
    return None if whole == 0 else part / whole


@dataclass(frozen=True)
class Contributor:
    """Someone the window expected something of, and what they declared.

    What was expected travels with what was declared, and never apart from
    it: five days read alone says nothing about whether the person is part
    time, on leave, or simply late in filling in their month.
    """

    id: int
    display_name: str
    declared_days: float
    expected_days: float

    @property
    def coverage(self) -> float | None:
        """Share of the expected time this person actually declared.

        None when the window expected nothing of them — a week of leave is
        not a failure, and a zero would read as one.
        """
        return _rate(self.declared_days, self.expected_days)


@dataclass(frozen=True)
class ActivitySummaryLine:
    """One mission over the window, and who put time on it.

    A project cut into work packages carries them: the portfolio is what the
    screen reads, not the internal breakdown. Everything the line answers —
    its days, its days for one person, what it moved — answers for the whole
    branch. `own_days` is the one exception, and exists so that an unfolded
    project does not show its total twice.
    """

    project_id: int
    label: str
    kind: ProjectKind
    status: ProjectStatus | None
    category: ProjectCategory | None
    #: Days booked on this line alone, per contributor id.
    days_by_contributor: dict[int, float] = field(default_factory=dict)
    #: Days booked on this line alone over the window before this one.
    previous_days: float = 0.0
    packages: tuple["ActivitySummaryLine", ...] = ()

    @property
    def own_days(self) -> float:
        """Days booked on this line, its packages left out."""
        return sum(self.days_by_contributor.values())

    @property
    def days(self) -> float:
        """Days booked on this mission, its packages counted in."""
        return self.own_days + sum(package.days for package in self.packages)

    def days_of(self, contributor_id: int) -> float:
        """What one person booked on this mission, packages counted in.

        Absent from the mapping is zero, not unknown: nobody declares an
        absence of work, and the cell is simply drawn empty.
        """
        return self.days_by_contributor.get(contributor_id, 0.0) + sum(
            package.days_of(contributor_id) for package in self.packages
        )

    @property
    def previous_total_days(self) -> float:
        """What the whole branch weighed over the window before."""
        return self.previous_days + sum(
            package.previous_total_days for package in self.packages
        )

    @property
    def movement(self) -> float:
        """Days gained or lost since the window before.

        What turns a table into a reading: a manager does not need to be told
        « 12 days on NOMAD », they need to be told it is three days down.
        """
        return self.days - self.previous_total_days

    @property
    def is_new(self) -> bool:
        """Whether the mission received nothing at all over the window before.

        Said apart from the movement: a mission appearing and a mission
        growing are two different pieces of news.
        """
        return self.previous_total_days == 0


@dataclass(frozen=True)
class ActivitySummary:
    """Everything the screen shows for one window.

    Missions and what happens around them are held apart, never folded
    together: leave and training are declared time too, and adding them in
    would leave no readable denominator for « 32 % of the time on WAATcher ».
    """

    period: Period
    contributors: tuple[Contributor, ...]
    projects: tuple[ActivitySummaryLine, ...]
    off_project: tuple[ActivitySummaryLine, ...]

    @property
    def project_days(self) -> float:
        return sum(line.days for line in self.projects)

    @property
    def off_project_days(self) -> float:
        return sum(line.days for line in self.off_project)

    @property
    def declared_days(self) -> float:
        return self.project_days + self.off_project_days

    @property
    def expected_days(self) -> float:
        """What the window called for, of everyone it names."""
        return sum(someone.expected_days for someone in self.contributors)

    @property
    def coverage(self) -> float | None:
        """How much of the expected time was declared.

        The figure that conditions every other one on the screen, and the
        reason it is shown before them rather than beside them.
        """
        return _rate(self.declared_days, self.expected_days)

    def share_of(self, days: float) -> float | None:
        """Weight of a slice of the declared time in the whole window."""
        return _rate(days, self.declared_days)
