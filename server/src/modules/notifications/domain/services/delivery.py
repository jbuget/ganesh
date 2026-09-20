"""Where a gesture lands: a new line, or the one already waiting."""

from src.modules.notifications.domain.entities.notification import Notification
from src.modules.notifications.domain.repositories.notification_repository import (
    NotificationRepository,
)


class NotificationDelivery:
    """Writes what a gesture owes, folding repeats into a single line.

    A domain service rather than a use case: every producer goes through it,
    and a use case may never call another. It holds the one rule that decides
    whether the bell stays readable — a month filled in cell by cell rings
    once, with a count, and not twenty-two times.
    """

    def __init__(self, notifications: NotificationRepository) -> None:
        self._notifications = notifications

    async def deliver(self, notifications: list[Notification]) -> None:
        for notification in notifications:
            await self._deliver_one(notification)

    async def _deliver_one(self, notification: Notification) -> None:
        if notification.kind.accumulates:
            twin = await self._notifications.find_open_twin(
                recipient_id=notification.recipient_id,
                kind=notification.kind,
                actor_id=notification.actor_id,
                day=notification.day,
            )
            if twin is not None:
                twin.absorb(at=notification.at)
                await self._notifications.save(twin)
                return
        await self._notifications.add(notification)
