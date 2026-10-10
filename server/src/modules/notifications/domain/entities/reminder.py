"""What one person is owed by letter: what is waiting, and how much of it.

The bell carries the detail and the read state. A letter carries the count of
what is waiting by kind, and — for the few most recent — who did what on which
project, with the address that opens it. Never what somebody *wrote*: a letter
is read on a lock screen and over a shoulder. The read state stays in the
inbox, which stops two places from disagreeing about what somebody has seen.
"""

from dataclasses import dataclass

from src.modules.notifications.domain.entities.notification import NotificationKind
from src.shared.exceptions.domain_exceptions import ValidationError


@dataclass(frozen=True)
class ReminderLine:
    """One kind of thing waiting, and how many of them there are."""

    kind: NotificationKind
    count: int


@dataclass(frozen=True)
class ReminderEntry:
    """One thing waiting, said as a line: who did what, on what, and where.

    `path` is an address on the client, never a full URL — the letter is what
    knows where the client lives. It is `None` when there is nothing left to
    open: a link to a 404 is worse than none.
    """

    who: str
    what: str
    about: str | None = None
    path: str | None = None
    repeated: int = 1


@dataclass(frozen=True)
class Reminder:
    """What one reader is owed, gathered by kind.

    Never empty: `roundup` answers nothing at all rather than building one
    with no lines. A letter that arrives saying nothing teaches its reader
    that it can be ignored, and the next one is too.
    """

    lines: tuple[ReminderLine, ...]
    #: The things waiting, most recent first. Empty is allowed: the counts
    #: above are what a letter cannot do without, the lines are what it adds.
    entries: tuple[ReminderEntry, ...] = ()

    def __post_init__(self) -> None:
        if not self.lines:
            raise ValidationError("A reminder with nothing in it is not one.")

    @property
    def total(self) -> int:
        """How many things are waiting, all kinds together."""
        return sum(line.count for line in self.lines)
