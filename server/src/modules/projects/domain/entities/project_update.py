"""An update posted on a mission."""

from dataclasses import dataclass
from datetime import datetime

from src.modules.projects.domain.entities.update_reaction import (
    Reaction,
    UpdateReaction,
)
from src.shared.exceptions.domain_exceptions import (
    ForbiddenActionError,
    ValidationError,
)


@dataclass
class ProjectUpdate:
    """What someone comes to say about how a mission is going.

    An update is not erased but marked deleted: the thread keeps its order and
    its replies, and the screen shows "Message supprime" there. Only its author
    may rewrite or withdraw it — a follow-up thread is not a wiki, everyone
    answers for their own words.
    """

    id: int | None
    project_id: int
    author_id: int
    body: str
    published_at: datetime
    edited_at: datetime | None = None
    deleted_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.deleted_at is not None:
            return
        self.body = self.body.strip()
        if not self.body:
            raise ValidationError("An update cannot be empty.")

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def _require_author(self, by: int) -> None:
        if by != self.author_id:
            raise ForbiddenActionError("Only the author of an update may change it.")

    def rewrite(self, body: str, by: int, at: datetime) -> None:
        self._require_author(by)
        if self.is_deleted:
            raise ForbiddenActionError("A deleted update cannot be rewritten.")

        new_one = body.strip()
        if not new_one:
            raise ValidationError("An update cannot be empty.")
        self.body = new_one
        self.edited_at = at

    def react(self, who: int, reaction: Reaction, at: datetime) -> UpdateReaction:
        """Answers without writing.

        Anyone may, including the author: a reaction is not applause one owes
        someone else. A withdrawn update is refused — there is nothing left to
        react to.
        """
        if self.is_deleted:
            raise ForbiddenActionError("A withdrawn update cannot be reacted to.")
        assert self.id is not None
        return UpdateReaction(update_id=self.id, user_id=who, reaction=reaction, at=at)

    def remove(self, by: int, at: datetime) -> None:
        self._require_author(by)
        if self.is_deleted:
            # Already withdrawn: the first date is the one that counts.
            return
        self.deleted_at = at
        self.body = ""
