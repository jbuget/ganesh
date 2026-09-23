"""What each function of the product saw, and what that is read from.

Ganesh is no longer one screen. The dashboard measured the grid alone, and
eleven other things were built beside it with nothing saying whether any of
them served. This is what says it.

**A surface is a function, not a screen.** Moving a card on the Kanban and
editing the same field on the project sheet write the very same
`project.status_change`, and declaring a day comes as readily from the grid
as from a terminal. The log records the gesture and never the door it came
through: a table naming screens would report « Kanban : 0 » on a month where
every card moved from a form. So the lines are named after what one does, and
`PHASE_PROGRESS` covers both doors by construction.

**What leaves no trace has no line.** The roadmap, the activity summary and
this very page only ever read, and nothing records that they were opened.
Giving them a line at zero would state a fact the register never held — the
same reason a roadmap never counts a bar as a go-live. They are named in
plain sight underneath instead, as what the table cannot see.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum

from src.modules.audit_logs.domain.entities.audit_log import AuditAction


class Surface(StrEnum):
    """A function of the product, as somebody would name what they did.

    The order declared here is the order the table reads in: the month one
    fills, the reference list one keeps, the portfolio one steers, then the
    team and what surrounds it. Fixed rather than sorted by usage — a table
    ordered by traffic buries the idle lines at the bottom, and those are the
    ones it exists to show.
    """

    TIME_ENTRY = "time_entry"
    MONTH_CLOSING = "month_closing"
    PROJECT_REGISTRY = "project_registry"
    PHASE_PROGRESS = "phase_progress"
    ASSIGNMENT = "assignment"
    PROJECT_UPDATES = "project_updates"
    PROJECT_FILES = "project_files"
    PLANNING = "planning"
    GAZETTE = "gazette"
    MOOD = "mood"
    NOTIFICATIONS = "notifications"
    REMINDERS = "reminders"
    PRESENCE = "presence"
    TEAM_ADMIN = "team_admin"
    API_KEYS = "api_keys"
    MACHINE_ACCESS = "machine_access"

    @classmethod
    def unlogged(cls) -> tuple["Surface", ...]:
        """The surfaces the audit log does not carry, each read elsewhere.

        Moods are outside the register by decision, a notification being read
        is nobody's gesture on a project, and a machine call is not a person's
        doing. Each is counted from its own table instead.
        """
        return (cls.MOOD, cls.NOTIFICATIONS, cls.MACHINE_ACCESS)


#: Which function each recorded gesture belongs to.
#:
#: Business knowledge, so it lives here rather than in a SQL `CASE`: it is
#: what lets one person who created a project and archived another count once.
#: A gesture missing from this map is a bug, and a test says so.
SURFACE_OF: dict[AuditAction, Surface] = {
    # Filling in a month: the days, and the projects one puts on one's grid.
    AuditAction.ENTRY_SET: Surface.TIME_ENTRY,
    AuditAction.ENTRY_CLEAR: Surface.TIME_ENTRY,
    AuditAction.MONTH_PROJECT_ADD: Surface.TIME_ENTRY,
    AuditAction.MONTH_PROJECT_REMOVE: Surface.TIME_ENTRY,
    # Closing it, and opening it again.
    AuditAction.MONTH_VALIDATE: Surface.MONTH_CLOSING,
    AuditAction.MONTH_REOPEN: Surface.MONTH_CLOSING,
    # Keeping the reference list.
    AuditAction.PROJECT_CREATE: Surface.PROJECT_REGISTRY,
    AuditAction.PROJECT_UPDATE: Surface.PROJECT_REGISTRY,
    AuditAction.PROJECT_DELETE: Surface.PROJECT_REGISTRY,
    # Moving the work along, from the board or from the sheet.
    AuditAction.PROJECT_STATUS_CHANGE: Surface.PHASE_PROGRESS,
    # Saying who is expected on what.
    AuditAction.PROJECT_ASSIGN: Surface.ASSIGNMENT,
    AuditAction.PROJECT_UNASSIGN: Surface.ASSIGNMENT,
    # Telling a project's news.
    AuditAction.UPDATE_POST: Surface.PROJECT_UPDATES,
    AuditAction.UPDATE_EDIT: Surface.PROJECT_UPDATES,
    AuditAction.UPDATE_REMOVE: Surface.PROJECT_UPDATES,
    # What a project carries besides words. A line of its own rather than one
    # shared with the thread: an image pasted into an update and a report
    # dropped on the tab are the same gesture on the same store, and the
    # question this table answers is whether that store serves at all.
    AuditAction.ATTACHMENT_ADD: Surface.PROJECT_FILES,
    AuditAction.ATTACHMENT_RENAME: Surface.PROJECT_FILES,
    AuditAction.ATTACHMENT_REMOVE: Surface.PROJECT_FILES,
    # Arbitrating what fits.
    AuditAction.SIMULATION_CREATE: Surface.PLANNING,
    AuditAction.SIMULATION_UPDATE: Surface.PLANNING,
    AuditAction.SIMULATION_DELETE: Surface.PLANNING,
    # Reading the month back.
    AuditAction.GAZETTE_GENERATE: Surface.GAZETTE,
    # Saying which days one works, and from where. A line of its own: it is
    # declared by everyone for themselves, and folded into team
    # administration it would read as a busy month at the manager's desk.
    AuditAction.USER_PRESENCE_DECLARE: Surface.PRESENCE,
    # Saying how often one is written to. A line of its own rather than one
    # shared with « Notifications », which counts notifications opened: mixing
    # a setting somebody changed into a figure of what people read would give
    # a number answering neither question. Zero here is a reading too — it
    # says the default is what everybody is still on.
    AuditAction.USER_REMINDER_CHOOSE: Surface.REMINDERS,
    # Holding the team.
    AuditAction.USER_CREATE: Surface.TEAM_ADMIN,
    AuditAction.USER_ROLE_CHANGE: Surface.TEAM_ADMIN,
    AuditAction.USER_IDENTITY_UPDATE: Surface.TEAM_ADMIN,
    AuditAction.USER_DEACTIVATE: Surface.TEAM_ADMIN,
    AuditAction.USER_ACTIVATE: Surface.TEAM_ADMIN,
    # Minting and cutting the keys. What they then reach is another line.
    AuditAction.API_KEY_CREATE: Surface.API_KEYS,
    AuditAction.API_KEY_UPDATE: Surface.API_KEYS,
    AuditAction.API_KEY_REVOKE: Surface.API_KEYS,
}


@dataclass(frozen=True)
class Trace:
    """One person's gestures of one kind over a window.

    Read as an aggregate and never as a list of log lines: the table counts
    people and gestures, and nothing here is meant to say who did what.
    """

    action: AuditAction
    actor_id: int
    gestures: int


@dataclass(frozen=True)
class Tally:
    """What a surface outside the log saw over a window."""

    people: int = 0
    gestures: int = 0


@dataclass(frozen=True)
class WindowReading:
    """Everything one window holds, from both sources."""

    traces: tuple[Trace, ...] = ()
    tallies: Mapping[Surface, Tally] = field(default_factory=dict)

    def tally_of(self, surface: Surface) -> Tally:
        return self.tallies.get(surface, Tally())


@dataclass(frozen=True)
class SurfaceActivity:
    """One line of the table: a function, and what it saw.

    People rather than gestures carry the movement. On a team of fifteen the
    number of gestures swings for nothing — one tidy-up afternoon doubles it
    — while a person who came or stopped coming is adoption itself.
    """

    surface: Surface
    people: int
    gestures: int
    previous_people: int
    #: The day it was last used, read beyond the window: « nothing this
    #: month » and « nothing since March » call for different decisions.
    #: None means nobody has ever used it.
    last_used_on: date | None = None

    @property
    def delta_in_people(self) -> int:
        return self.people - self.previous_people

    @property
    def is_idle(self) -> bool:
        """Nobody used it over the window."""
        return self.gestures == 0

    @property
    def never_used(self) -> bool:
        return self.last_used_on is None


@dataclass(frozen=True)
class SurfaceUsage:
    """What the whole product saw over a window, function by function."""

    activities: tuple[SurfaceActivity, ...]

    @property
    def idle_count(self) -> int:
        """Functions nobody used. The figure one acts on by deleting code."""
        return sum(1 for activity in self.activities if activity.is_idle)
