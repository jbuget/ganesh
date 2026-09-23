"""Gathering what is waiting for one reader into what a letter says."""

from collections.abc import Iterable

from src.modules.notifications.domain.entities.notification import (
    Notification,
    NotificationKind,
)
from src.modules.notifications.domain.entities.reminder import Reminder, ReminderLine


def roundup(waiting: Iterable[Notification]) -> Reminder | None:
    """What one reader is owed, by kind, or nothing at all.

    Two rules, and both are what keep the letter worth opening:

    **Nothing waiting is no letter.** Answering `None` rather than an empty
    reminder puts the rule here, where it is tested, instead of in whoever
    calls next.

    **A folded line counts once.** A month filled in cell by cell carries a
    count of twenty-two and is still one thing to go and read: the letter says
    how much is waiting, not how many gestures made it.

    The kinds come out in the order the domain declares them, never by count. A
    letter whose lines moved about from one morning to the next would have to
    be read afresh every time.
    """
    counted: dict[NotificationKind, int] = {}
    for notification in waiting:
        counted[notification.kind] = counted.get(notification.kind, 0) + 1

    if not counted:
        return None

    return Reminder(
        lines=tuple(
            ReminderLine(kind=kind, count=counted[kind])
            for kind in NotificationKind
            if kind in counted
        )
    )
