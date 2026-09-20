"""Port for what people are told."""

from abc import ABC, abstractmethod
from datetime import date, datetime

from src.modules.notifications.domain.entities.notification import (
    Notification,
    NotificationKind,
)


class NotificationRepository(ABC):
    """Persistence contract for notifications."""

    @abstractmethod
    async def add(self, notification: Notification) -> Notification: ...

    @abstractmethod
    async def save(self, notification: Notification) -> None:
        """Writes back a line that was already there."""
        ...

    @abstractmethod
    async def find_open_twin(
        self,
        recipient_id: int,
        kind: NotificationKind,
        actor_id: int,
        day: date | None,
    ) -> Notification | None:
        """The same gesture, by the same person, still waiting to be seen.

        What lets a month filled in cell by cell ring once. A line already
        read is not a twin: having seen yesterday's edits says nothing of
        today's.
        """
        ...

    @abstractmethod
    async def list_for(
        self, recipient_id: int, unread_only: bool, limit: int, offset: int
    ) -> list[Notification]:
        """One person's notifications, the most recent first."""
        ...

    @abstractmethod
    async def count_for(self, recipient_id: int, unread_only: bool) -> int: ...

    @abstractmethod
    async def set_read_state(
        self,
        recipient_id: int,
        ids: list[int] | None,
        read: bool,
        at: datetime,
    ) -> int:
        """Marks lines seen, or puts them back in waiting. `None` means all.

        Filtering by recipient is the repository's job and not the caller's:
        knowing the id of someone else's notification must never be enough to
        touch it. Returns how many lines actually changed.
        """
        ...
