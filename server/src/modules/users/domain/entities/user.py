"""Ganesh user, and the rights that come with their role."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum

from src.shared.enums.department import Department
from src.shared.enums.org_level import OrgLevel
from src.shared.exceptions.domain_exceptions import ValidationError

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

    **The declaration order is the ladder**, from the least to the most, and
    `rank` reads nothing else: a rung inserted in the middle lifts everything
    above it, which is what one wants. An account comes into being at the
    bottom, and somebody already above says afterwards who is behind it.
    """

    #: What an unknown identity gets. The whole company signs in through the
    #: same Entra tenant, so being recognised at the door says nothing about
    #: belonging to the team: this role opens nothing on its own. It is named
    #: after what the person *is* — of the company, not of the team — rather
    #: than after the one thing they may do today, which is to express a need.
    GUEST = "GUEST"
    TEAMMATE = "TEAMMATE"
    MANAGER = "MANAGER"
    #: A manager who also mints accounts and names their peers. The top rung,
    #: and the only one that may confer itself on somebody else.
    ADMIN = "ADMIN"

    @property
    def rank(self) -> int:
        """Where this role stands on the ladder. Higher is more."""
        return _RANK[self]

    def reaches(self, other: "Role") -> bool:
        """Whether this role stands at least as high as `other`."""
        return self.rank >= other.rank


#: Built from the declaration order, which the class above commits to.
_RANK: dict[Role, int] = {
    role: rank for rank, role in enumerate(Role.__members__.values())
}


@dataclass
class User:
    """A team member, provisioned from Microsoft Entra ID."""

    id: int | None
    entra_oid: str
    email: str
    display_name: str
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

    def __post_init__(self) -> None:
        self.email = self.email.strip().lower()
        self.first_name = _trimmed(self.first_name)
        self.last_name = _trimmed(self.last_name)
        self.github_username = _handle(self.github_username)

    @classmethod
    def declared(
        cls,
        email: str,
        first_name: str,
        last_name: str,
        role: Role,
        department: Department | None = None,
        github_username: str | None = None,
        org_level: OrgLevel | None = None,
    ) -> "User":
        """An account made to exist before its owner has ever signed in.

        Declaring somebody is saying who they are, so the civil name is asked
        for rather than left optional: without it the account reads as the
        address it was typed at, which is exactly what waiting for the first
        sign-in already gives, at no cost. Entra writes its own display name
        that day; until then the name the team reads is the one given here.

        No Entra id is carried — « » is how the entity says « never signed
        in », and the repository stores it as `NULL`. The account is claimed at
        that first sign-in, matched on the address alone, which is therefore
        the one thing to get right.
        """
        address = _trimmed(email)
        given, family = _trimmed(first_name), _trimmed(last_name)
        if not address:
            raise ValidationError("An account is declared at an address.")
        if not given or not family:
            raise ValidationError("Declaring somebody is saying who they are.")
        return cls(
            id=None,
            entra_oid="",
            email=address,
            display_name=f"{given} {family}",
            role=role,
            first_name=given,
            last_name=family,
            department=department,
            github_username=github_username,
            org_level=org_level,
        )

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
    def is_admin(self) -> bool:
        """The top rung, and the only one that may confer itself."""
        return self.role is Role.ADMIN

    @property
    def is_manager(self) -> bool:
        """Whether this account steers the team: a manager, or an admin above.

        Everything a manager decides is read through here — reopening a month,
        arbitrating a need, importing the reference list. An admin is a manager
        who also mints accounts and names their peers: turning them away here
        would make the top of the ladder weaker than the rung below it.
        """
        return self.role.reaches(Role.MANAGER)

    @property
    def is_guest(self) -> bool:
        """Whether this account belongs to the company but not to the team.

        It is the one thing the door reads: every screen of the application is
        closed to a guest, and the requests open themselves to them, one route
        at a time.
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

    def can_edit_open_months(self) -> bool:
        """Anyone on the team may edit an open month, a colleague's included.

        A guest holds no month: they declare no time, and the grid is not a
        screen they ever reach.
        """
        return self.is_active and not self.is_guest

    def can_declare_user(self) -> bool:
        """Whether this account may make another exist before it signs in.

        A manager and an admin both may: waiting for somebody's first sign-in
        to attach them to a mission is a wait nobody chose, and whoever fills
        in a teammate's sheet is the one who knows they are arriving.
        """
        return self.is_active and self.is_manager

    def can_grant(self, role: Role) -> bool:
        """Nobody confers a rank above their own.

        Which is what makes the ladder one: a manager who could name an admin
        would be an admin with one extra click.
        """
        return self.can_manage_teammates() and self.role.reaches(role)

    def can_change_role_of(self, target: "User", role: Role) -> bool:
        """Tells whether this account may put `target` at `role`.

        Two rules hold the whole thing, and the last admin is protected by
        them rather than by a rule of their own:

        - **Nobody changes their own rank.** Demoting oneself is a one-way
          trip — the account reaches no route that could promote it back.
        - **Nobody acts on somebody above them, nor confers above
          themselves.** A manager must not be able to demote the admin, or
          the rung above would hold nothing.
        """
        if target.id == self.id:
            return False
        return self.can_grant(role) and self.role.reaches(target.role)

    def can_deactivate(self, target: "User") -> bool:
        """Tells whether this manager may cut `target` off.

        Nobody deactivates themselves: the account would be turned away at the
        door on the very next request, and no one could reopen it from inside.
        Nor does anyone cut off a rank above their own — a manager shutting the
        admin out would be the same one-way trip, taken on somebody else.
        """
        return (
            self.can_manage_teammates()
            and target.id != self.id
            and self.role.reaches(target.role)
        )

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
