"""What one person is owed by letter: what is waiting, and how much of it.

The bell carries the detail and the read state. A letter carries neither — it
says how much is waiting and of what kind, and leads back to the inbox. It
points; it does not copy. That is what lets it stay three lines long, and what
stops two places from disagreeing about what somebody has seen.
"""

from dataclasses import dataclass

from src.modules.notifications.domain.entities.notification import NotificationKind


@dataclass(frozen=True)
class ReminderLine:
    """One kind of thing waiting, and how many of them there are."""

    kind: NotificationKind
    count: int


@dataclass(frozen=True)
class Reminder:
    """What one reader is owed, gathered by kind.

    Never empty: `roundup` answers nothing at all rather than building one
    with no lines. A letter that arrives saying nothing teaches its reader
    that it can be ignored, and the next one is too.
    """

    lines: tuple[ReminderLine, ...]

    def __post_init__(self) -> None:
        if not self.lines:
            raise ValueError("A reminder with nothing in it is not one.")

    @property
    def total(self) -> int:
        """How many things are waiting, all kinds together."""
        return sum(line.count for line in self.lines)
