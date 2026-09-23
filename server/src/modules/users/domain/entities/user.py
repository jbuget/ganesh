"""Ganesh user, and the rights that come with their role."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum

from src.modules.users.domain.entities.presence import WeekPresence
from src.modules.users.domain.entities.reminder_cadence import ReminderCadence
from src.shared.enums.department import Department

#: Below this, a fresh login is not worth a write to the database.
#:
#: The API is sessionless: a bearer token is presented on every request, and
#: the only thing it can observe is "this teammate was here". Without this
#: window, the column would measure nothing but HTTP traffic.
LOGIN_FRESHNESS = timedelta(minutes=15)


def _trimmed(value: str | None) -> str | None:
    """« », «   » and « nothing » all say the same: nothing is known."""
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _handle(value: str | None) -> str | None:
    """The handle alone, however it was written.

    « @lea-chen » is how one writes a GitHub handle; « lea-chen » is what it
    is, and what an address is built from.
    """
    trimmed = _trimmed(value)
    return _trimmed(trimmed.lstrip("@")) if trimmed else None


class Role(StrEnum):
    """What a user is allowed to do."""

    TEAMMATE = "TEAMMATE"
    MANAGER = "MANAGER"


@dataclass
class User:
    """A team member, provisioned from Microsoft Entra ID."""

    id: int | None
    entra_oid: str
    email: str
    display_name: str
    role: Role = Role.TEAMMATE
    is_active: bool = field(default=True)
    last_login_at: datetime | None = None
    #: Civil name, told apart from the display name Entra provides: « L. Chen »
    #: identifies an account, it does not tell who one is talking to.
    first_name: str | None = None
    last_name: str | None = None
    #: The department this teammate belongs to. Named from the same list as the
    #: missions: steering compares the two sides, and cannot if the names drift.
    department: Department | None = None
    #: The handle alone — « lea-chen », never « @lea-chen » nor a full URL:
    #: it is what the profile address is built from.
    github_username: str | None = None
    #: The ordinary week: which days one works, and from where. On site every
    #: day until somebody says otherwise — the arrangement the team runs on,
    #: so it is what is true of anyone who has said nothing, not a placeholder
    #: standing in for an answer.
    presence: WeekPresence = field(default_factory=WeekPresence)
    #: How often this teammate wants the letter saying what is waiting. Every
    #: day until they say otherwise: somebody who has never opened the setting
    #: is precisely the reader the bell is failing to reach.
    reminder_cadence: ReminderCadence = ReminderCadence.DAILY

    def __post_init__(self) -> None:
        self.email = self.email.strip().lower()
        self.first_name = _trimmed(self.first_name)
        self.last_name = _trimmed(self.last_name)
        self.github_username = _handle(self.github_username)

    def set_identity(
        self,
        first_name: str | None,
        last_name: str | None,
        department: Department | None,
        github_username: str | None,
    ) -> None:
        """Gives away who this teammate is, and where they work.

        The four go together: the sheet is written as a whole, and a field
        left out is a field one has decided to empty.
        """
        self.first_name = _trimmed(first_name)
        self.last_name = _trimmed(last_name)
        self.department = department
        self.github_username = _handle(github_username)

    @property
    def label(self) -> str:
        """The name one reads, everywhere the application names this teammate.

        « Prénom Nom » as soon as anyone has said who is behind the account.
        Entra only ever names the account — « L. Chen » identifies a mailbox,
        it does not say who one is talking to — so it stands in and no more.
        """
        civil = " ".join(part for part in (self.first_name, self.last_name) if part)
        return civil or self.display_name

    @property
    def is_manager(self) -> bool:
        return self.role is Role.MANAGER

    def can_reopen_month(self) -> bool:
        """Only a manager can reopen a validated month."""
        return self.is_active and self.is_manager

    def can_manage_teammates(self) -> bool:
        """Managing teammates is reserved for managers."""
        return self.is_active and self.is_manager

    def can_edit_open_months(self) -> bool:
        """Anyone may edit an open month, a colleague's included."""
        return self.is_active

    def can_declare_own_presence(self) -> bool:
        """Everyone says their own week, and nobody else's.

        No manager's business: where somebody works from is a fact about them,
        and relaying it would only put a delay between the fact and the board
        the team reads.
        """
        return self.is_active

    def can_choose_own_reminder(self) -> bool:
        """Everyone says how often they are written to, and nobody else does.

        No manager's business, for the same reason a declared week is not: how
        often somebody wants their mailbox used is a fact about them.
        """
        return self.is_active

    def choose_reminder_cadence(self, cadence: ReminderCadence) -> None:
        """Takes down how often this teammate wants to be written to."""
        self.reminder_cadence = cadence

    def can_deactivate(self, target: "User") -> bool:
        """Tells whether this manager may cut `target` off.

        Nobody deactivates themselves: the account would be turned away at the
        door on the very next request, and no one could reopen it from inside.
        """
        return self.can_manage_teammates() and target.id != self.id

    def record_login(
        self, at: datetime, freshness: timedelta = LOGIN_FRESHNESS
    ) -> bool:
        """Stamps this teammate's visit. Tells whether it is worth persisting.

        The stamp never moves backwards: two concurrent requests may arrive out
        of order, and the last known login stays the most recent one.
        """
        previous = self.last_login_at
        if previous is not None and at - previous < freshness:
            return False
        self.last_login_at = at
        return True
