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

    A closed catalogue: it grows by adding a member, never by a wildcard. Each
    one names what a route needs, not what a screen shows.
    """

    CATALOG_READ = "catalog:read"
    PROJECTS_READ = "projects:read"
    PROJECTS_WRITE = "projects:write"
    ENTRIES_READ = "entries:read"


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
        return not self.is_revoked and not self.is_expired(now)

    def grants(self, scope: ApiKeyScope) -> bool:
        return scope in self.scopes

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
