"""What a read of the audit log hands back."""

from dataclasses import dataclass
from datetime import datetime

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.projects.domain.entities.project import Project
from src.modules.users.domain.entities.user import User


@dataclass(frozen=True)
class SignedAuditLog:
    """One line of the log, and what it names.

    All of it is optional: a line survives the account and the mission it names
    being removed, and a log that dropped what it can no longer sign would be
    rewriting history.
    """

    log: AuditLog
    actor: User | None
    target_user: User | None
    #: The mission the line is about, named only where the reader is not
    #: already inside it. A mission's own log leaves it out: the page is the
    #: mission, and repeating its name on every line would say nothing.
    project: Project | None = None


@dataclass(frozen=True)
class AuditLogPage:
    """One page of the log, and how long the log is.

    The count is of the whole log rather than of the page: it is what tells a
    screen whether there is more to ask for, and how much of it has been read.
    """

    entries: list[SignedAuditLog]
    total: int


@dataclass(frozen=True)
class TouchedProject:
    """A project the register saw move, and the gesture that moved it.

    The project is named by its identifier alone: whoever asks holds the
    reference list already, and repeating a label here would be handing back a
    name that a rename has since made wrong.
    """

    project_id: int
    action: AuditAction
    at: datetime
