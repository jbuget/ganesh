"""A service account and the key that lets it in.

A key belongs to a machine, never to a person. It opens nothing on its own:
a route has to ask for one of its scopes, one route at a time.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum

from src.shared.exceptions.domain_exceptions import (
    ForbiddenActionError,
    ValidationError,
)

#: Below this, a fresh call is not worth a write to the database. Same
#: reasoning as `LOGIN_FRESHNESS`: without a window, the column would measure
#: HTTP traffic rather than use.
USE_FRESHNESS = timedelta(minutes=15)

NAME_MAX_LENGTH = 64


class ApiKeyScope(StrEnum):
    """What a key is allowed to reach.

    A closed catalogue, `resource:verb`. Each member names what a route needs,
    not what a screen shows.

    Two of them are broad, one per verb: `all:read` covers every read,
    `all:write` every write. They are independent — a key that both reads and
    writes everything carries the two — and they are real members rather than a
    pattern matched at run time, so a key can still be read off the table and
    told what it opens.

    What they cover includes scopes that **do not exist yet**: that is the
    price of breadth, and the reason the form says so.
    """

    ALL_READ = "all:read"
    ALL_WRITE = "all:write"
    CATALOG_READ = "catalog:read"
    PROJECTS_READ = "projects:read"
    PROJECTS_WRITE = "projects:write"
    ENTRIES_READ = "entries:read"

    @property
    def is_read(self) -> bool:
        return self.value.endswith(":read")


class ApiKeyState(StrEnum):
    """What a key is worth right now, as the badge reads it.

    Derived, never stored: `revoked_at` and `expires_at` are the facts, this is
    what they add up to. Revocation wins over expiry — the cut is the fact that
    matters, and a key cut before its date is not « expirée ».
    """

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass
class ApiKey:
    """A service account: what it is called, who answers for it, what it opens."""

    id: int | None
    #: The machine it serves — « CI waat-tools ». The whole team reads it, so
    #: it is written for them and not for its author.
    name: str
    #: The public half of the key. Not a secret: it is only a lookup handle.
    public_id: str
    secret_hash: str
    #: The human who answers for what this machine does.
    owner_id: int
    #: The manager who minted it. Not always the owner.
    created_by: int
    scopes: list[ApiKeyScope] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None
    revoked_by: int | None = None

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        if not self.name:
            raise ValidationError("A key must be named.")
        if len(self.name) > NAME_MAX_LENGTH:
            raise ValidationError(
                f"A key name cannot exceed {NAME_MAX_LENGTH} characters."
            )

        # A key with no scope reaches nothing. It is not an error to hold one,
        # but there is no reason to mint one.
        self.scopes = list(dict.fromkeys(self.scopes))
        if not self.scopes:
            raise ValidationError("A key must carry at least one scope.")

        if self.expires_at is not None and self.expires_at <= self.created_at:
            raise ValidationError("An expiry date must come after the creation.")

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    def is_expired(self, now: datetime) -> bool:
        return self.expires_at is not None and self.expires_at <= now

    def is_usable(self, now: datetime) -> bool:
        """Whether the key itself stands in the way. The owner is checked apart."""
        return self.state_at(now) is ApiKeyState.ACTIVE

    def state_at(self, now: datetime) -> ApiKeyState:
        """What the key is worth, the cut weighing more than the date."""
        if self.is_revoked:
            return ApiKeyState.REVOKED
        if self.is_expired(now):
            return ApiKeyState.EXPIRED
        return ApiKeyState.ACTIVE

    def grants(self, scope: ApiKeyScope) -> bool:
        """Whether the key opens what a route asks for.

        A broad scope covers the precise ones **of its own verb**, and no
        other: writing does not imply reading. Two switches rather than a
        ladder — a key that does both says so by carrying both, and one that
        only writes is not granted every read behind the reader's back.
        """
        if scope in self.scopes:
            return True
        broad = ApiKeyScope.ALL_READ if scope.is_read else ApiKeyScope.ALL_WRITE
        return broad in self.scopes

    def rename(self, name: str) -> None:
        """Changes what the table calls it. Refused once the key is cut.

        A revoked key is a piece of the audit: it says what a machine was
        called while it worked, and renaming it afterwards would rewrite that.
        """
        self._ensure_still_open()
        self.name = name
        self.__post_init__()

    def set_scopes(self, scopes: list[ApiKeyScope]) -> None:
        """Replaces what the key opens. The screen sends what it displays."""
        self._ensure_still_open()
        self.scopes = scopes
        self.__post_init__()

    def _ensure_still_open(self) -> None:
        if self.is_revoked:
            raise ForbiddenActionError("A revoked key can no longer be changed.")

    def revoke(self, by: int, at: datetime) -> None:
        """Cuts the key for good.

        Revoking twice does not restamp: the first cut is the one that counts,
        and it is the one the audit already recorded.
        """
        if self.is_revoked:
            raise ForbiddenActionError("This key has already been revoked.")
        self.revoked_at = at
        self.revoked_by = by

    def record_use(self, at: datetime, freshness: timedelta = USE_FRESHNESS) -> bool:
        """Stamps a call. Tells whether it is worth persisting.

        The stamp never moves backwards: two concurrent calls may arrive out of
        order, and the last known use stays the most recent one.
        """
        previous = self.last_used_at
        if previous is not None and at - previous < freshness:
            return False
        self.last_used_at = at
        return True
