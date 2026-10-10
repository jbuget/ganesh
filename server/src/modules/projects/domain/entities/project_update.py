"""An update posted on a mission."""

from dataclasses import dataclass
from datetime import datetime

from src.modules.projects.domain.entities.thread_message import ThreadMessage
from src.modules.projects.domain.entities.update_comment import UpdateComment
from src.modules.projects.domain.entities.update_reaction import (
    Reaction,
    UpdateReaction,
)
from src.shared.exceptions.domain_exceptions import ForbiddenActionError


@dataclass
class ProjectUpdate(ThreadMessage):
    """What someone comes to say about how a mission is going.

    An update is not erased but marked deleted: the thread keeps its order and
    its replies, and the screen shows "Message supprime" there. Only its author
    may rewrite or withdraw it — a follow-up thread is not a wiki, everyone
    answers for their own words.
    """

    project_id: int

    NOUN = "update"
    A_NOUN = "an update"

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

    def reply(self, who: int, body: str, at: datetime) -> UpdateComment:
        """Answers it in the thread, under it rather than beside it.

        Anyone who may write may answer, the author included: a follow-up
        thread is a conversation, not a right of reply. A withdrawn update is
        refused — there is nothing left to answer, and the replies already
        written keep their place under it.
        """
        if self.is_deleted:
            raise ForbiddenActionError("A withdrawn update cannot be answered.")
        assert self.id is not None
        return UpdateComment(
            id=None,
            update_id=self.id,
            author_id=who,
            body=body,
            published_at=at,
        )
