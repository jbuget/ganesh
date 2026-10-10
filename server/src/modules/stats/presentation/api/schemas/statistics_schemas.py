"""Dashboard schemas.

Every rate is nullable: a window may expect nothing of anyone, and the screen
draws that differently from a zero.
"""

from datetime import date

from pydantic import BaseModel

from src.modules.calendar.domain.entities.period import PeriodRange
from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.projects.domain.entities.project import ProjectCategory, ProjectStatus
from src.modules.stats.domain.entities.surface_usage import Surface
from src.shared.enums.team import Team
from src.shared.enums.work_nature import WorkNature


class PeriodResponse(BaseModel):
    """The window the figures were read over."""

    range: PeriodRange
    start: date
    end: date
    working_days: int


class CoverageResponse(BaseModel):
    """How much of the expected time was declared."""

    declared_days: float
    expected_days: float
    missing_days: float
    rate: float | None
    delta_in_points: float | None
    #: Whose time it is read over: one team, never the whole company.
    team: Team
    #: How many people that team counts. None leaves nothing to read.
    people: int


class CoveragePointResponse(BaseModel):
    """The coverage of one week."""

    week_start: date
    declared_days: float
    expected_days: float
    rate: float | None


class ActivityDayResponse(BaseModel):
    """The gestures the register holds for one day."""

    day: date
    gestures: int


class FreshnessResponse(BaseModel):
    """How long days waited before being declared."""

    entries: int
    median_delay: float | None
    day_to_day_share: float | None
    late_share: float | None


class MonthValidationResponse(BaseModel):
    """Closed months, and those that were locked."""

    validated: int
    due: int
    rate: float | None


class TeammateResponse(BaseModel):
    id: int
    display_name: str


class AdoptionResponse(BaseModel):
    """How much of the team took part."""

    contributors: int
    expected_contributors: int
    rate: float | None
    idle: list[TeammateResponse]


class SurfaceActivityResponse(BaseModel):
    """What one function of the product saw over the window."""

    surface: Surface
    people: int
    gestures: int
    #: Movement in people, never in gestures: one tidy-up afternoon doubles
    #: the second, while somebody who came or stopped coming is adoption.
    delta_in_people: int
    #: Nobody used it over the window. Carried rather than left to the screen
    #: to work out: the count above it reads the same rule, and the two must
    #: not be able to drift apart.
    is_idle: bool
    #: Read beyond the window, and null when nobody has ever used it.
    last_used_on: date | None


class SurfaceUsageResponse(BaseModel):
    """What the product saw, function by function, in a fixed order."""

    activities: list[SurfaceActivityResponse]
    idle_count: int


class StatusShareResponse(BaseModel):
    """Time booked in one project phase."""

    status: ProjectStatus
    days: float
    share: float | None


class CategoryShareResponse(BaseModel):
    """Time booked on one strategic axis. A null axis carries none."""

    category: ProjectCategory | None
    days: float
    share: float | None


class NatureShareResponse(BaseModel):
    """Project time booked under one trade. A null trade states none."""

    nature: WorkNature | None
    days: float
    share: float | None


class MissionShareResponse(BaseModel):
    """Time booked against one mission."""

    project_id: int
    label: str
    days: float
    share: float | None


class SteeringResponse(BaseModel):
    """Where the declared time went."""

    project_days: float
    off_project_days: float
    project_share: float | None
    by_status: list[StatusShareResponse]
    by_category: list[CategoryShareResponse]
    by_nature: list[NatureShareResponse]
    top_missions: list[MissionShareResponse]


class RegistryResponse(BaseModel):
    """Whether the mission reference list still matches the real work."""

    active_missions: int
    missions_with_time: int
    missions_without_time: int
    usage_rate: float | None
    created: int
    without_activity: int
    unbudgeted: int
    followed: int
    published: int


class IntakeResponse(BaseModel):
    """What the company asked for over the window, and what became of it."""

    submitted: int
    accepted: int
    rejected: int
    deferred: int
    converted: int
    #: Still waiting for an answer, however long ago they were handed over.
    waiting: int
    #: The longest wait among them, in days. Null when none waits.
    oldest_wait_days: int | None


class AccountsResponse(BaseModel):
    """Who has an account, and how far each one has been let in."""

    guests: int
    teammates: int
    managers: int
    admins: int
    never_signed_in: int
    reminders_daily: int
    reminders_weekly: int
    reminders_never: int
    #: Share of the accounts a letter can reach that asked for one.
    reminder_rate: float | None


class StewardshipResponse(BaseModel):
    """Whether somebody answers for each project."""

    active_projects: int
    without_lead: int
    without_tech_lead: int


class ThreadResponse(BaseModel):
    """Whether the follow-up thread is a conversation or a noticeboard."""

    posted: int
    answered: int
    #: Share of the updates somebody other than their author answered.
    answer_rate: float | None
    followed: int
    #: Followed projects with no news for longer than a fortnight.
    silent: int


class KindReadingResponse(BaseModel):
    """What one kind of notification sent, and how much was opened."""

    kind: NotificationKind
    delivered: int
    read: int
    read_rate: float | None


class NotificationReadingResponse(BaseModel):
    """Whether what the product says is heard."""

    delivered: int
    read: int
    read_rate: float | None
    #: Waiting right now, whenever they were written.
    unread: int
    #: Of those, left unopened for longer than a fortnight.
    ignored: int
    #: The least opened first.
    kinds: list[KindReadingResponse]


class StatisticsResponse(BaseModel):
    """Everything the dashboard shows for one window."""

    period: PeriodResponse
    coverage: CoverageResponse
    #: The last weeks, oldest first, whatever window was asked for.
    coverage_trend: list[CoveragePointResponse]
    #: Every day of the year ending today, oldest first, quiet ones included.
    activity: list[ActivityDayResponse]
    freshness: FreshnessResponse
    month_validation: MonthValidationResponse
    adoption: AdoptionResponse
    surfaces: SurfaceUsageResponse
    steering: SteeringResponse
    registry: RegistryResponse
    intake: IntakeResponse
    accounts: AccountsResponse
    stewardship: StewardshipResponse
    thread: ThreadResponse
    notification_reading: NotificationReadingResponse
