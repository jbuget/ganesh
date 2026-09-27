"""A reply written under an update."""

from dataclasses import dataclass
from datetime import datetime

from src.modules.projects.domain.entities.comment_reaction import CommentReaction
from src.modules.projects.domain.entities.thread_message import ThreadMessage
from src.modules.projects.domain.entities.update_reaction import Reaction
from src.shared.exceptions.domain_exceptions import ForbiddenActionError


@dataclass
class UpdateComment(ThreadMessage):
    """What one answers under an update, rather than beside it.

    A comment hangs off an update and nothing hangs off a comment: the depth
    is carried by the table rather than by a rule, so no gesture can ever
    make it deeper. A conversation three levels down is one nobody reads to
    the end, and the thread of a mission is read to know where it stands.

    It carries none of what steers: no flag for the revue, no place in the
    count the board announces, nothing the reference list reads. Those belong
    to the update it answers — one puts a subject on the agenda, not a reply
    to it. That is why it is an entity of its own rather than an update
    pointing at another: an entity defined by what it does not carry is in
    the wrong place.
    """

    update_id: int

    NOUN = "comment"
    A_NOUN = "a comment"

    def react(self, who: int, reaction: Reaction, at: datetime) -> CommentReaction:
        """Answers a reply without writing another one.

        The same rule as above it: anyone may, the author included, and a
        withdrawn comment is refused — there is nothing left to react to.
        """
        if self.is_deleted:
            raise ForbiddenActionError("A withdrawn comment cannot be reacted to.")
        assert self.id is not None
        return CommentReaction(
            comment_id=self.id, user_id=who, reaction=reaction, at=at
        )
