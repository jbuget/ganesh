"""Turns one gesture into the lines it owes to the people it concerns."""

from collections.abc import Iterable
from datetime import date, datetime
from typing import Any

from src.modules.notifications.domain.entities.notification import (
    Notification,
    NotificationKind,
)


def notify(
    kind: NotificationKind,
    actor_id: int,
    recipients: Iterable[int],
    at: datetime,
    project_id: int | None = None,
    day: date | None = None,
    payload: dict[str, Any] | None = None,
) -> list[Notification]:
    """The notifications one gesture owes, in the order the recipients came.

    Pure on purpose: it reads no repository. Who is concerned is worked out by
    the use case, which already holds what it takes to know — and that is what
    keeps this module from importing any other.

    Two things happen here, and nowhere else: the person who acted is taken
    out, and someone named twice is told once.
    """
    seen: set[int] = {actor_id}
    notifications: list[Notification] = []
    for recipient_id in recipients:
        if recipient_id in seen:
            continue
        seen.add(recipient_id)
        notifications.append(
            Notification(
                recipient_id=recipient_id,
                kind=kind,
                actor_id=actor_id,
                at=at,
                project_id=project_id,
                day=day,
                payload=payload,
            )
        )
    return notifications
