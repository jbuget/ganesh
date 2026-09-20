"""What a notification refuses, and what it does when the same thing happens twice."""

from datetime import date, datetime

import pytest

from src.modules.notifications.domain.entities.notification import (
    Notification,
    NotificationKind,
)
from src.shared.exceptions.domain_exceptions import ValidationError

MONDAY = datetime(2026, 1, 12, 9, 0)
TUESDAY = datetime(2026, 1, 13, 9, 0)


def a_notification(**overrides) -> Notification:
    fields = {
        "recipient_id": 1,
        "kind": NotificationKind.PROJECT_ASSIGNED,
        "actor_id": 2,
        "at": MONDAY,
    } | overrides
    return Notification(**fields)


def test_a_notification_refuses_to_name_its_recipient_as_actor() -> None:
    with pytest.raises(ValidationError):
        a_notification(recipient_id=7, actor_id=7)


def test_a_fresh_notification_is_unread_and_counts_one() -> None:
    notification = a_notification()

    assert notification.is_read is False
    assert notification.count == 1


def test_reading_a_notification_stamps_the_moment() -> None:
    notification = a_notification()

    notification.mark_read(at=TUESDAY)

    assert notification.is_read is True
    assert notification.read_at == TUESDAY


def test_reading_twice_keeps_the_first_moment() -> None:
    notification = a_notification()
    notification.mark_read(at=MONDAY)

    notification.mark_read(at=TUESDAY)

    assert notification.read_at == MONDAY


def test_putting_a_notification_back_in_waiting_clears_the_moment() -> None:
    notification = a_notification()
    notification.mark_read(at=MONDAY)

    notification.mark_unread()

    assert notification.is_read is False
    assert notification.read_at is None


def test_the_same_gesture_again_counts_up_and_comes_back_to_the_top() -> None:
    """Twenty half-days posted on a month make one line, not twenty."""
    notification = a_notification(day=date(2026, 1, 1))

    notification.absorb(at=TUESDAY)

    assert notification.count == 2
    assert notification.at == TUESDAY


def test_absorbing_a_read_notification_makes_it_wait_again() -> None:
    """One has seen what was done yesterday, not what is being done now."""
    notification = a_notification(day=date(2026, 1, 1))
    notification.mark_read(at=MONDAY)

    notification.absorb(at=TUESDAY)

    assert notification.is_read is False
    assert notification.count == 2
