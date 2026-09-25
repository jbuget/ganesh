"""Ganesh user, and the rights that come with their role."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum

from src.modules.users.domain.entities.presence import WeekPresence
from src.modules.users.domain.entities.reminder_cadence import ReminderCadence
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
    """What a user is allowed to do, from the door to the platform.

    The order is a fact the whole application reads: nobody hands out a role
    above their own, and a role is only ever changed by someone who holds at
    least as much. Declaring them from the least to the most empowered is
    therefore what makes `RANK` below say the truth.
    """

    #: Whoever has just signed in and nothing more. The whole company comes
    #: through the same Entra tenant, so this is what being recognised at the
    #: door gets one: a role that opens nothing but one's own needs, until
    #: somebody says who they are on the team.
    GUEST = "GUEST"
    TEAMMATE = "TEAMMATE"
    MANAGER = "MANAGER"
    #: A manager, plus the platform itself: the administration screen, and the
    #: one role a manager cannot hand out.
    ADMIN = "ADMIN"


#: Where each role stands on the ladder. Written from `Role` rather than by
#: hand, so a role added between two others cannot be forgotten here.
RANK: dict[Role, int] = {Role(role): position for position, role in enumerate(Role)}


@dataclass
class User:
    """A team member, provisioned from Microsoft Entra ID."""

    id: int | None
    entra_oid: str
    email: str
    display_name: str
    #: A guest until somebody says otherwise: what is true of an account
    #: nobody has declared, not a placeholder standing in for an answer.
    role: Role = Role.GUEST
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
    #: The ordinary week: which days one works, and from where. On site every
    #: day until somebody says otherwise — the arrangement the team runs on,
    #: so it is what is true of anyone who has said nothing, not a placeholder
    #: standing in for an answer.
    presence: WeekPresence = field(default_factory=WeekPresence)
    #: How often this teammate wants the letter saying what is waiting. Every
    #: day until they say otherwise: somebody who has never opened the setting
    #: is precisely the reader the bell is failing to reach.
    reminder_cadence: ReminderCadence = ReminderCadence.DAILY
    #: When the last letter actually went out. `None` until the first one
    #: does — and a letter that failed leaves it where it was, so the next run
    #: considers the same window again. That is the only retry there is.
    reminder_sent_at: datetime | None = None

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
        """Whether this account reaches as far as a manager does.

        An admin does: the ladder is one axis, and a role above manager holds
        everything a manager holds. Reading it as « the role is MANAGER »
        would mean every screen listing both, and one of them forgetting to.
        """
        return self.holds(Role.MANAGER)

    @property
    def is_admin(self) -> bool:
        return self.role is Role.ADMIN

    def holds(self, role: Role) -> bool:
        """Whether this account stands at `role` on the ladder, or above."""
        return RANK[self.role] >= RANK[role]

    def can_write(self) -> bool:
        """Whether this account may enter anything at all.

        A guest reads the application whole and writes nothing into it: a
        month, a project, a mise à jour, a mood. The rule is one line here so
        that every use case that writes asks the same question, and the day a
        role is added nobody has to remember which side of it it falls on.
        """
        return self.is_active and not self.is_guest

    def can_administrate(self) -> bool:
        """Only an admin opens the administration of the platform."""
        return self.is_active and self.is_admin

    @property
    def is_guest(self) -> bool:
        """Whether this account only ever comes to ask for something.

        It is the one thing the door reads: every screen of the application is
        closed to a guest, and the requests open themselves to them.
        """
        return self.role is Role.GUEST

    def can_reopen_month(self) -> bool:
        """Only a manager can reopen a validated month."""
        return self.is_active and self.is_manager

    def can_manage_teammates(self) -> bool:
        """Managing teammates is reserved for managers."""
        return self.is_active and self.is_manager

    def can_arbitrate_requests(self) -> bool:
        """Weighing what the company asks for is reserved for managers.

        Whether this particular manager may weigh this particular request is
        another question, and the request answers it: nobody arbitrates what
        they asked for or what they carry.
        """
        return self.is_active and self.is_manager

    def can_change_role_of(self, target: "User", role: Role) -> bool:
        """Tells whether this user may move `target` to `role`.

        Two bounds, read the same way: nobody hands out a role above their
        own, and nobody moves someone who stands above them. A manager
        therefore promotes up to manager and leaves an admin alone — being
        able to demote the one who could undo it is the same door read
        backwards.

        Nobody changes their own role either, for the reason nobody
        deactivates themselves: an admin demoting themselves would leave the
        platform short of an administrator, with no way back in from inside.
        """
        if not self.can_manage_teammates() or target.id == self.id:
            return False
        return self.holds(role) and self.holds(target.role)

    def can_edit_open_months(self) -> bool:
        """Anyone on the team may edit an open month, a colleague's included.

        A guest holds no month: they declare no time, and the grid is not a
        screen they ever reach.
        """
        return self.can_write()

    def can_declare_own_presence(self) -> bool:
        """Everyone says their own week, and nobody else's.

        No manager's business: where somebody works from is a fact about them,
        and relaying it would only put a delay between the fact and the board
        the team reads.
        """
        return self.can_write()

    def can_choose_own_reminder(self) -> bool:
        """Everyone says how often they are written to, and nobody else does.

        No manager's business, for the same reason a declared week is not: how
        often somebody wants their mailbox used is a fact about them.
        """
        return self.can_write()

    def choose_reminder_cadence(self, cadence: ReminderCadence) -> None:
        """Takes down how often this teammate wants to be written to."""
        self.reminder_cadence = cadence

    def stamp_reminder(self, at: datetime) -> None:
        """Takes down that a letter went out, so the next one starts after it.

        Called once a letter has actually been handed over, never before: a
        stamp moved on a letter that failed would lose what it announced.
        """
        self.reminder_sent_at = at

    def can_run_reminders(self) -> bool:
        """Only a manager sends the round by hand.

        It writes to the whole team at once, which is a gesture nobody should
        be able to make by wandering into a screen — and the one reason it
        exists is to repair a morning the clock got wrong.
        """
        return self.is_active and self.is_manager

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
