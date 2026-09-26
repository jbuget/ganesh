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
    #: When somebody said this deserved discussing at the next revue, and who.
    #: Cleared in the meeting: a mark nobody ever lowers stops meaning anything
    #: once every thread carries one.
    flagged_at: datetime | None = None
    flagged_by: int | None = None
    cleared_at: datetime | None = None
    cleared_by: int | None = None

    def __post_init__(self) -> None:
        if self.deleted_at is not None:
            return
        self.body = self.body.strip()
        if not self.body:
            raise ValidationError("An update cannot be empty.")

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def is_flagged(self) -> bool:
        """Whether it is waiting to be discussed.

        Raised and not yet lowered. A round that is over leaves both dates
        behind, which is what lets the same subject be raised again.
        """
        return self.flagged_at is not None and self.cleared_at is None

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

    def flag(self, by: int, at: datetime) -> None:
        """Puts it on the agenda of the next revue.

        Anybody may, the author included: it is a reader noticing that
        something has to be said out loud, and reserving the gesture to
        whoever wrote the words would miss exactly that. Raising it twice
        changes nothing — whoever raised it is who raised it.
        """
        if self.is_deleted:
            raise ForbiddenActionError("A withdrawn update cannot be flagged.")
        if self.is_flagged:
            return
        self.flagged_at = at
        self.flagged_by = by
        self.cleared_at = None
        self.cleared_by = None

    def clear(self, by: int, at: datetime) -> None:
        """Takes it off the agenda, the revue having read it.

        A gesture of the meeting rather than of whoever raised it, so anybody
        may: what is discussed is discussed for everyone. Lowering what was
        never raised is a no-op.
        """
        if not self.is_flagged:
            return
        self.cleared_at = at
        self.cleared_by = by

    def remove(self, by: int, at: datetime) -> None:
        self._require_author(by)
        if self.is_deleted:
            # Already withdrawn: the first date is the one that counts.
            return
        self.deleted_at = at
        self.body = ""
        # Nothing left to discuss: the words the mark pointed at are gone.
        self.flagged_at = None
        self.flagged_by = None
        self.cleared_at = None
        self.cleared_by = None
