"""Marking notifications seen, or putting them back in waiting."""

from datetime import datetime

from src.modules.notifications.application.dtos.notification_dtos import (
    ReadStateCommand,
    ReadStateOutcome,
)
from src.modules.notifications.domain.repositories.notification_repository import (
    NotificationRepository,
)


class SetNotificationsReadStateUseCase:
    """Moves lines between seen and waiting, one, several, or all of them.

    One use case for the four gestures rather than four: they differ by two
    fields and would otherwise say the same thing four times. Whose inbox is
    being touched is settled in the repository, so that knowing the id of
    someone else's line never opens it.
    """

    def __init__(self, notifications: NotificationRepository) -> None:
        self._notifications = notifications

    async def execute(
        self, command: ReadStateCommand, now: datetime | None = None
    ) -> ReadStateOutcome:
        updated = await self._notifications.set_read_state(
            recipient_id=command.recipient_id,
            ids=command.ids,
            read=command.read,
            at=now or datetime.now(),
        )
        return ReadStateOutcome(
            updated=updated,
            unread_count=await self._notifications.count_for(
                command.recipient_id, unread_only=True
            ),
        )
