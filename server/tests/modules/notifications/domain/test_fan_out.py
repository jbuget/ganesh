"""Who a gesture reaches, once the person who made it is taken out."""

from datetime import date, datetime

from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.domain.services.fan_out import notify

NOW = datetime(2026, 1, 12, 9, 0)


def test_a_gesture_reaches_everyone_it_concerns() -> None:
    notifications = notify(
        NotificationKind.PROJECT_UPDATE_POSTED,
        actor_id=1,
        recipients=[2, 3],
        at=NOW,
        project_id=42,
    )

    assert [n.recipient_id for n in notifications] == [2, 3]
    assert {n.project_id for n in notifications} == {42}
    assert {n.kind for n in notifications} == {NotificationKind.PROJECT_UPDATE_POSTED}


def test_the_one_who_made_the_gesture_is_never_told_of_it() -> None:
    notifications = notify(
        NotificationKind.PROJECT_UPDATE_POSTED,
        actor_id=1,
        recipients=[1, 2],
        at=NOW,
        project_id=42,
    )

    assert [n.recipient_id for n in notifications] == [2]


def test_someone_named_twice_is_told_once() -> None:
    """A referent who is also a contributor is one person, not two."""
    notifications = notify(
        NotificationKind.PROJECT_STATUS_CHANGED,
        actor_id=1,
        recipients=[3, 2, 3],
        at=NOW,
        project_id=42,
    )

    assert [n.recipient_id for n in notifications] == [3, 2]


def test_a_gesture_that_concerns_nobody_else_rings_nowhere() -> None:
    assert (
        notify(NotificationKind.PROJECT_ASSIGNED, actor_id=1, recipients=[1], at=NOW)
        == []
    )


def test_what_is_carried_reaches_every_recipient() -> None:
    notifications = notify(
        NotificationKind.TIMESHEET_EDITED,
        actor_id=1,
        recipients=[2, 3],
        at=NOW,
        day=date(2026, 1, 1),
        payload={"month": "2026-01"},
    )

    assert {n.day for n in notifications} == {date(2026, 1, 1)}
    assert {n.at for n in notifications} == {NOW}
    assert all(n.payload == {"month": "2026-01"} for n in notifications)
