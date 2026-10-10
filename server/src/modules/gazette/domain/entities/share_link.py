"""A link that lets anybody who holds it read one version of a digest.

The link names a **version**, never a month: a digest is never rewritten, and
what an outsider quotes has to still be what they read. Sharing a regeneration
means making another link.

It opens for as long as nobody closes it — there is no date it lapses on, and
no setting to ask for one. What stands in for it is that every link is listed
for the whole team, with who made it and when, so one left in a mail from last
year is one somebody can see and take back.
"""

import secrets
from dataclasses import dataclass
from datetime import datetime

from src.shared.exceptions.domain_exceptions import ValidationError

#: Bytes of randomness behind a token. Thirty-two make a string nobody guesses,
#: and none of it is derived from the digest or from who asked: a token that
#: could be computed from an id would be a door that opens for whoever counts.
TOKEN_BYTES = 32

#: What a token is refused under, whatever drew it.
MIN_TOKEN_LENGTH = 40


@dataclass
class ShareLink:
    """One way in to one version of one digest."""

    digest_id: int
    token: str
    created_by_id: int
    created_at: datetime
    revoked_at: datetime | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        if len(self.token) < MIN_TOKEN_LENGTH:
            raise ValidationError("A share token is long enough not to be guessed.")

    @classmethod
    def open(cls, digest_id: int, created_by_id: int, at: datetime) -> "ShareLink":
        """A new link, with a token drawn for it."""
        return cls(
            digest_id=digest_id,
            token=secrets.token_urlsafe(TOKEN_BYTES),
            created_by_id=created_by_id,
            created_at=at,
        )

    @property
    def is_open(self) -> bool:
        return self.revoked_at is None

    def revoke(self, at: datetime) -> None:
        """Closes it. Closing a closed link keeps the first date, as a
        withdrawal does: what counts is when it stopped being open."""
        if self.is_open:
            self.revoked_at = at
