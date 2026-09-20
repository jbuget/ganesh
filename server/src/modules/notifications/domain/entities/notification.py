"""What one person is told, and whether they have seen it.

The audit log says what happened on a project; a notification says what
concerns me. One gesture writes a single line of log but as many
notifications as there are people it concerns, and whether it has been seen
belongs to each of them — which is why the two are not the same table.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any

from src.shared.exceptions.domain_exceptions import ValidationError


class NotificationKind(StrEnum):
    """What one is being told about.

    Named after the gesture, in the domain's vocabulary; the French the reader
    gets is composed by the interface, as it is for the audit log.
    """

    # Who is expected on a mission.
    PROJECT_ASSIGNED = "project.assigned"
    PROJECT_UNASSIGNED = "project.unassigned"

    # What is done to my month. There is no « month.validated »: nobody may
    # validate somebody else's month — the domain refuses it — so a line
    # saying so could never be written.
    TIMESHEET_EDITED = "timesheet.edited"
    MONTH_REOPENED = "month.reopened"

    # The life of a mission I am on.
    PROJECT_UPDATE_POSTED = "project.update_posted"
    PROJECT_STATUS_CHANGED = "project.status_changed"
    PROJECT_ARCHIVED = "project.archived"
    PROJECT_DELETED = "project.deleted"

    # What is done to my account.
    USER_ROLE_CHANGED = "user.role_changed"
    USER_DEACTIVATED = "user.deactivated"
    USER_ACTIVATED = "user.activated"
    API_KEY_CREATED = "api_key.created"
    API_KEY_REVOKED = "api_key.revoked"

    # Someone is talking to me.
    UPDATE_MENTION = "update.mention"

    @property
    def accumulates(self) -> bool:
        """Whether a repeat of the same gesture folds into the waiting line.

        Filling in a colleague's month writes twenty-two entries and must ring
        once. Everything else is a gesture one makes on purpose, and each one
        deserves its own line: validating a month twice never happens, and two
        updates posted on a mission are two things to read.
        """
        return self is NotificationKind.TIMESHEET_EDITED


@dataclass
class Notification:
    """One thing someone is told, waiting to be seen.

    `day` carries the month for everything that concerns a timesheet, and the
    day nothing else: it is what makes two edits on the same month fold into
    one line and two edits on two months stay apart.
    """

    recipient_id: int
    kind: NotificationKind
    actor_id: int
    at: datetime = field(default_factory=datetime.now)
    project_id: int | None = None
    day: date | None = None
    payload: dict[str, Any] | None = None
    count: int = 1
    read_at: datetime | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        # The rule the whole feature leans on: a gesture never rings for the
        # person who made it, or every move would come back as an echo.
        if self.recipient_id == self.actor_id:
            raise ValidationError("Nobody is notified of what they did themselves.")

    @property
    def is_read(self) -> bool:
        return self.read_at is not None

    def mark_read(self, at: datetime) -> None:
        """Seen. The first moment is the one that counts."""
        if self.read_at is None:
            self.read_at = at

    def mark_unread(self) -> None:
        """Put back in waiting, to be dealt with later."""
        self.read_at = None

    def absorb(self, at: datetime) -> None:
        """Folds one more of the same gesture into this line.

        It comes back to the top and waits again: having seen what was done
        yesterday says nothing of what is being done now.
        """
        self.count += 1
        self.at = at
        self.read_at = None
