"""Turns a read of the inbox into what the screens receive."""

from src.modules.notifications.application.dtos.notification_dtos import (
    NotificationFeed,
    ReadStateOutcome,
    SignedNotification,
)
from src.modules.notifications.presentation.api.schemas.notification_schemas import (
    NotificationFeedResponse,
    NotificationPersonResponse,
    NotificationProjectResponse,
    NotificationResponse,
    ReadStateResponse,
)
from src.shared.utils.initials import initials


def to_notification_response(signed: SignedNotification) -> NotificationResponse:
    line = signed.notification
    assert line.id is not None
    return NotificationResponse(
        id=line.id,
        at=line.at,
        kind=line.kind,
        actor=(
            None
            if signed.actor is None
            else NotificationPersonResponse(
                id=signed.actor.id or 0,
                display_name=signed.actor.label,
                initials=initials(signed.actor.label),
            )
        ),
        project=(
            None
            if signed.project is None or signed.project.id is None
            else NotificationProjectResponse(
                id=signed.project.id, label=signed.project.label
            )
        ),
        day=line.day,
        count=line.count,
        read_at=line.read_at,
        payload=line.payload,
    )


def to_feed_response(feed: NotificationFeed) -> NotificationFeedResponse:
    return NotificationFeedResponse(
        total=feed.total,
        unread_count=feed.unread_count,
        entries=[to_notification_response(entry) for entry in feed.entries],
    )


def to_read_state_response(outcome: ReadStateOutcome) -> ReadStateResponse:
    return ReadStateResponse(updated=outcome.updated, unread_count=outcome.unread_count)
