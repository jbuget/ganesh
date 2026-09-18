"""Timesheet user, and the rights that come with their role."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum

#: Below this, a fresh login is not worth a write to the database.
#:
#: The API is sessionless: a bearer token is presented on every request, and
#: the only thing it can observe is "this teammate was here". Without this
#: window, the column would measure nothing but HTTP traffic.
LOGIN_FRESHNESS = timedelta(minutes=15)


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

    def __post_init__(self) -> None:
        self.email = self.email.strip().lower()

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
