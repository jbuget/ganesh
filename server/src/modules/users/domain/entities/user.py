"""Ganesh user, and the rights that come with their role."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum

from src.shared.enums.department import Department
from src.shared.enums.org_level import OrgLevel

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
    """What a user is allowed to do.

    Declared from the least to the most: an account comes into being as a
    requester, and a manager says afterwards who is behind it.
    """

    #: Someone who comes to express a need, and does nothing else here. The
    #: whole company signs in through the same Entra tenant, so this is what
    #: an unknown identity gets: a role that opens nothing on its own.
    REQUESTER = "REQUESTER"
    TEAMMATE = "TEAMMATE"
    MANAGER = "MANAGER"


@dataclass
class User:
    """A team member, provisioned from Microsoft Entra ID."""

    id: int | None
    entra_oid: str
    email: str
    display_name: str
    role: Role = Role.REQUESTER
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
    #: Where this person stands in the company. Left unsaid for most: it is
    #: filled in for whoever has to be told apart — a sponsor of needs, today.
    org_level: OrgLevel | None = None

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
        org_level: OrgLevel | None,
    ) -> None:
        """Gives away who this teammate is, and where they work.

        The five go together: the sheet is written as a whole, and a field
        left out is a field one has decided to empty.
        """
        self.first_name = _trimmed(first_name)
        self.last_name = _trimmed(last_name)
        self.department = department
        self.github_username = _handle(github_username)
        self.org_level = org_level

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

    @property
    def is_requester(self) -> bool:
        """Whether this account only ever comes to ask for something.

        It is the one thing the door reads: every screen of the application is
        closed to a requester, and the requests open themselves to them.
        """
        return self.role is Role.REQUESTER

    def can_reopen_month(self) -> bool:
        """Only a manager can reopen a validated month."""
        return self.is_active and self.is_manager

    def can_manage_teammates(self) -> bool:
        """Managing teammates is reserved for managers."""
        return self.is_active and self.is_manager

    def can_edit_open_months(self) -> bool:
        """Anyone on the team may edit an open month, a colleague's included.

        A requester holds no month: they declare no time, and the grid is not
        a screen they ever reach.
        """
        return self.is_active and not self.is_requester

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
