"""What a read of the audit log hands back."""

from dataclasses import dataclass

from src.modules.audit_logs.domain.entities.audit_log import AuditLog
from src.modules.users.domain.entities.user import User


@dataclass(frozen=True)
class SignedAuditLog:
    """One line of the log, and the people it names.

    Both are optional: a line survives the account it names being removed, and
    a log that dropped what it can no longer sign would be rewriting history.
    """

    log: AuditLog
    actor: User | None
    target_user: User | None


@dataclass(frozen=True)
class AuditLogPage:
    """One page of the log, and how long the log is.

    The count is of the whole log rather than of the page: it is what tells a
    screen whether there is more to ask for, and how much of it has been read.
    """

    entries: list[SignedAuditLog]
    total: int
