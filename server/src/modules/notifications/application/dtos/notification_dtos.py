"""What a read of the inbox hands back, and what a write asks for."""

from dataclasses import dataclass

from src.modules.notifications.domain.entities.notification import Notification
from src.modules.projects.domain.entities.project import Project
from src.modules.users.domain.entities.user import User


@dataclass(frozen=True)
class SignedNotification:
    """A notification, and what it takes to say it in French.

    Both are optional, and for the same reason the audit log allows it: an
    account may have been removed, a mission may have been deleted, and a line
    that dropped what it can no longer name would rewrite what one was told.
    """

    notification: Notification
    actor: User | None
    project: Project | None


@dataclass(frozen=True)
class NotificationFeed:
    """One page of the inbox, and what the bell needs.

    `unread_count` travels with the page rather than on a route of its own:
    the bell and the panel ask the same question, and asking it twice would
    let the two disagree.
    """

    entries: list[SignedNotification]
    total: int
    unread_count: int


@dataclass(frozen=True)
class ReadStateCommand:
    """Request to mark lines seen, or to put them back in waiting.

    `ids` at `None` means every line of the inbox — what the « tout marquer
    comme lu » button asks for.
    """

    recipient_id: int
    ids: list[int] | None
    read: bool


@dataclass(frozen=True)
class ReadStateOutcome:
    """What a write on the inbox changed, and what is left waiting.

    The count travels back with the answer so the bell settles without asking
    again: a screen that had to refetch to find out would show the old figure
    for as long as the round trip takes.
    """

    updated: int
    unread_count: int
