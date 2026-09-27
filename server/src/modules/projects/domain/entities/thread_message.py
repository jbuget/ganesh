"""Words somebody signed in a thread."""

from dataclasses import dataclass
from datetime import datetime

from src.shared.exceptions.domain_exceptions import (
    ForbiddenActionError,
    ValidationError,
)


@dataclass(kw_only=True)
class ThreadMessage:
    """What an update and the replies it draws both are.

    Not an abstraction for its own sake: « only the author rewrites or
    withdraws » is one rule, and written twice it is two chances to fix it
    once. A thread is not a wiki — everyone answers for their own words —
    and that holds as much for a line of a conversation as for the subject
    it hangs under.

    Nothing is erased: a withdrawal sets a date and empties the text. The
    message keeps its place and its signature, so what was said around it
    keeps its order and its context.

    The fields are keyword-only, which is what lets each entity keep its own
    required field — a mission for an update, the update for a reply —
    without it having to come first.

    What is *not* shared stays on each: an update goes on the agenda of a
    revue, and a reply does not.
    """

    id: int | None
    author_id: int
    body: str
    published_at: datetime
    edited_at: datetime | None = None
    deleted_at: datetime | None = None

    #: How a refusal names this kind of message. « update » and « comment »
    #: are two different things to whoever reads the error, and one that
    #: named the wrong one would send the reader to the wrong screen.
    NOUN = "message"
    A_NOUN = "a message"

    def __post_init__(self) -> None:
        if self.deleted_at is not None:
            return
        self.body = self._not_empty(self.body)

    @classmethod
    def _not_empty(cls, body: str) -> str:
        trimmed = body.strip()
        if not trimmed:
            raise ValidationError(f"{cls.A_NOUN.capitalize()} cannot be empty.")
        return trimmed

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def _require_author(self, by: int) -> None:
        if by != self.author_id:
            raise ForbiddenActionError(
                f"Only the author of {self.A_NOUN} may change it."
            )

    def rewrite(self, body: str, by: int, at: datetime) -> None:
        self._require_author(by)
        if self.is_deleted:
            raise ForbiddenActionError(f"A deleted {self.NOUN} cannot be rewritten.")
        self.body = self._not_empty(body)
        self.edited_at = at

    def remove(self, by: int, at: datetime) -> None:
        self._require_author(by)
        if self.is_deleted:
            # Already withdrawn: the first date is the one that counts.
            return
        self.deleted_at = at
        self.body = ""
