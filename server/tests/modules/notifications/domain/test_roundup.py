"""Gathering what is waiting into what a letter says."""

from datetime import date, datetime

from src.modules.notifications.domain.entities.notification import (
    Notification,
    NotificationKind,
)
from src.modules.notifications.domain.services.roundup import roundup

AT = datetime(2026, 9, 23, 9, 0)


def waiting(kind: NotificationKind, count: int = 1) -> Notification:
    return Notification(
        recipient_id=2,
        kind=kind,
        actor_id=7,
        at=AT,
        day=date(2026, 9, 1) if count > 1 else None,
        count=count,
    )


class TestWhatALetterGathers:
    def test_one_kind_of_thing_makes_one_line(self) -> None:
        reminder = roundup(
            [
                waiting(NotificationKind.UPDATE_MENTION),
                waiting(NotificationKind.UPDATE_MENTION),
            ]
        )

        assert reminder is not None
        assert len(reminder.lines) == 1
        assert reminder.lines[0].kind is NotificationKind.UPDATE_MENTION
        assert reminder.lines[0].count == 2

    def test_several_kinds_make_several_lines(self) -> None:
        reminder = roundup(
            [
                waiting(NotificationKind.UPDATE_MENTION),
                waiting(NotificationKind.MONTH_REOPENED),
                waiting(NotificationKind.UPDATE_MENTION),
            ]
        )

        assert reminder is not None
        assert len(reminder.lines) == 2
        assert reminder.total == 3

    def test_a_folded_line_counts_once(self) -> None:
        # A month filled in cell by cell is one line in the inbox, whatever
        # the bell shows beside it. The letter says how much is waiting to be
        # read, not how many gestures made it.
        reminder = roundup([waiting(NotificationKind.TIMESHEET_EDITED, count=22)])

        assert reminder is not None
        assert reminder.lines[0].count == 1
        assert reminder.total == 1

    def test_the_kinds_read_in_the_order_the_domain_declares_them(self) -> None:
        # Fixed rather than by count: a letter whose lines moved about from one
        # morning to the next would have to be read afresh every time.
        reminder = roundup(
            [
                waiting(NotificationKind.UPDATE_MENTION),
                waiting(NotificationKind.PROJECT_ASSIGNED),
            ]
        )

        assert reminder is not None
        assert [line.kind for line in reminder.lines] == [
            NotificationKind.PROJECT_ASSIGNED,
            NotificationKind.UPDATE_MENTION,
        ]


class TestNothingIsNeverALetter:
    def test_nothing_waiting_is_no_reminder_at_all(self) -> None:
        assert roundup([]) is None
