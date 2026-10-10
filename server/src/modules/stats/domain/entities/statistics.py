"""The figures the dashboard reads, and the rules behind them.

Every rate here can be unknown. A period may expect nothing of anyone — a
weekend, a team with nobody in it, a window closing no month — and in that
case a zero would read as a failure that is not one. `None` says "there is
nothing to read", which is a different statement, and the screen draws it
differently.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, timedelta
from statistics import median

from src.modules.calendar.domain.entities.period import Period
from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.projects.domain.entities.project import ProjectCategory, ProjectStatus
from src.modules.stats.domain.entities.surface_usage import SurfaceUsage
from src.shared.enums.team import Team
from src.shared.enums.work_nature import WorkNature

#: Up to this delay, an entry was still written from memory of the day itself.
DAY_TO_DAY_DELAY = 2

#: Beyond this, the day is reconstructed rather than remembered: whatever is
#: declared then says more about the calendar than about the work.
LATE_DELAY = 15


#: Past this many days without a word, a project the team keeps an eye on has
#: gone quiet. The thread is reworked twice a week and read at the weekly
#: review: a fortnight with nothing means two reviews missed.
SILENT_AFTER_DAYS = 14

#: Past this many days unopened, a notification is no longer waiting to be
#: read: it has been left.
IGNORED_AFTER_DAYS = 14


def age_in_days(day: date, today: date) -> int:
    """How many days ago `day` was. Never negative: a clock skewed by a few
    hours must not draw a wait of minus one day."""
    return max(0, (today - day).days)


def ignored_before(today: date) -> date:
    """The day before which an unopened notification counts as left."""
    return today - timedelta(days=IGNORED_AFTER_DAYS)


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
class CoveragePoint:
    """The coverage of one week: one point of the curve the headline leads.

    A single figure says where the team stands, and a series says where it is
    going — whether adoption climbs, stalls, or fell back after a reminder.
    """

    week_start: date
    declared_days: float
    expected_days: float

    @property
    def rate(self) -> float | None:
        return _rate(self.declared_days, self.expected_days)


@dataclass(frozen=True)
class CoverageScope:
    """Whose time the coverage is read over, said beside the figure.

    A rate measured on one team and read as the whole company's is the
    misreading this exists to prevent — and it explains a figure nobody can
    read yet: nobody placed in the team leaves nothing to divide.
    """

    team: Team
    people: int


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
    #: Project time per trade. None carries what was booked under none: the
    #: days the reprise took over, which nobody ever declared a trade for.
    by_nature: dict[WorkNature | None, float] = field(default_factory=dict)
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
    #: Active missions no day can be booked against: the entry is refused until
    #: one trade is added, and the sheet says so.
    without_activity: int = 0
    #: Active missions cut into trades, one of which has no budget: the
    #: mission then reads as unestimated rather than as half of one.
    unbudgeted: int = 0
    #: Active missions the team keeps an eye on right now.
    followed: int = 0
    #: Active missions published to the catalogue.
    published: int = 0

    @property
    def missions_without_time(self) -> int:
        """Active missions nobody booked a single half day against."""
        return max(0, self.active_missions - self.missions_with_time)

    @property
    def usage_rate(self) -> float | None:
        return _rate(self.missions_with_time, self.active_missions)


@dataclass(frozen=True)
class Accounts:
    """Who has an account, and how far each one has been let in.

    Counts and never names: the dashboard says how many are waiting at the
    door, the team administration says who they are.
    """

    #: Signed in once, and not yet told apart from anybody: they reach the
    #: recueil and nothing else until a manager says whose account it is.
    guests: int
    teammates: int
    managers: int
    admins: int
    #: Accounts that can declare but nobody ever signed into: a role handed
    #: out before anybody logged in, and not used since.
    never_signed_in: int
    #: How often those accounts asked to be written to. Guests are never
    #: written to and are counted in none of these three.
    reminders_daily: int
    reminders_weekly: int
    reminders_never: int

    @property
    def reachable_by_letter(self) -> int:
        return self.reminders_daily + self.reminders_weekly + self.reminders_never

    @property
    def reminder_rate(self) -> float | None:
        """Share of the accounts a letter can reach that asked for one."""
        return _rate(
            self.reminders_daily + self.reminders_weekly, self.reachable_by_letter
        )


@dataclass(frozen=True)
class Stewardship:
    """Whether somebody answers for each project.

    A technical lead is who to call when the service breaks, and the title
    outlives the work: a project with none sends its next bug to nobody.
    Counted over projects alone — a work package answers to the project above
    it, and off-project work has no service to break.
    """

    active_projects: int
    without_lead: int
    without_tech_lead: int


@dataclass(frozen=True)
class Thread:
    """Whether the follow-up thread is a conversation or a noticeboard."""

    #: Updates posted during the window, withdrawn ones left out.
    posted: int
    #: Of those, the ones somebody other than their author answered, in words
    #: or by a sign. Answering oneself is not the team answering.
    answered: int
    #: For each project the team follows, the age in days of its latest
    #: update. None when nothing was ever said: as silent as it gets.
    followed_news_ages: list[int | None] = field(default_factory=list)

    @property
    def answer_rate(self) -> float | None:
        return _rate(self.answered, self.posted)

    @property
    def followed(self) -> int:
        return len(self.followed_news_ages)

    @property
    def silent(self) -> int:
        """Followed projects with no news for longer than a fortnight."""
        return sum(
            1
            for age in self.followed_news_ages
            if age is None or age > SILENT_AFTER_DAYS
        )


@dataclass(frozen=True)
class KindReading:
    """What one kind of notification sent, and how much of it was opened."""

    kind: NotificationKind
    delivered: int
    read: int

    @property
    def read_rate(self) -> float | None:
        return _rate(self.read, self.delivered)


@dataclass(frozen=True)
class NotificationReading:
    """Whether what the product says is heard.

    Read over the notifications written during the window, kind by kind, with
    the backlog beside it: a line opened is a line that served, and one left
    for weeks is the product talking to nobody.
    """

    #: The least opened first: it is the one a team acts on. When two are
    #: equally opened, the bigger one, since five unopened lines say more
    #: than one.
    kinds: list[KindReading]
    #: Waiting right now, whenever they were written.
    unread: int
    #: Of those, the ones left unopened for longer than a fortnight.
    ignored: int

    @classmethod
    def of(
        cls,
        per_kind: dict[NotificationKind, tuple[int, int]],
        unread: int,
        ignored: int,
    ) -> "NotificationReading":
        """Reads what was sent and opened per kind, ordered the way it is shown."""
        kinds = [
            KindReading(kind=kind, delivered=delivered, read=read)
            for kind, (delivered, read) in per_kind.items()
        ]
        kinds.sort(key=lambda one: (one.read_rate or 0.0, -one.delivered))
        return cls(kinds=kinds, unread=unread, ignored=ignored)

    @property
    def delivered(self) -> int:
        return sum(kind.delivered for kind in self.kinds)

    @property
    def read(self) -> int:
        return sum(kind.read for kind in self.kinds)

    @property
    def read_rate(self) -> float | None:
        return _rate(self.read, self.delivered)


@dataclass(frozen=True)
class Intake:
    """What the company asked for over the window, and what became of it.

    Counted apart from the missions, as the recueil itself is: a need is not a
    mission, and a month that filed six and built none says something neither
    figure says alone. A draft makes no movement and appears nowhere here.
    """

    #: Handed over to be weighed.
    submitted: int
    #: Said yes to. A need already turned into a mission was accepted first,
    #: and that yes still counts.
    accepted: int
    rejected: int
    #: « Not now »: neither a yes nor a no, and the answer most get.
    deferred: int
    #: Became a mission.
    converted: int
    #: How long each need still waiting for an answer has waited, in days.
    #: Read over the whole backlog, however old: a need nobody answered is
    #: not forgiven by the window moving past the day it was handed over.
    waiting_days: list[int] = field(default_factory=list)

    @property
    def waiting(self) -> int:
        return len(self.waiting_days)

    @property
    def oldest_wait_days(self) -> int | None:
        return max(self.waiting_days, default=None)


@dataclass(frozen=True)
class Statistics:
    """Everything the dashboard shows for one window.

    The lead figure comes with the one before it: a coverage rate says little
    on its own, and much once it is read as moving.
    """

    period: Period
    coverage: Coverage
    previous_coverage: Coverage
    coverage_scope: CoverageScope
    #: The weeks leading up to today, oldest first, whatever the window is.
    coverage_trend: list[CoveragePoint]
    freshness: Freshness
    month_validation: MonthValidation
    adoption: Adoption
    surfaces: SurfaceUsage
    steering: Steering
    registry: Registry
    intake: Intake
    accounts: Accounts
    stewardship: Stewardship
    thread: Thread
    notification_reading: NotificationReading

    @property
    def coverage_delta_in_points(self) -> float | None:
        return self.coverage.delta_in_points(self.previous_coverage)
