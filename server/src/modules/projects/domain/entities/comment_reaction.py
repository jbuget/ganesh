"""A reaction left on a comment."""

from dataclasses import dataclass
from datetime import datetime

from src.modules.projects.domain.entities.update_reaction import Reaction


@dataclass(frozen=True)
class CommentReaction:
    """One person, one sign, on one comment.

    The same set of signs as under an update — `Reaction` is declared once and
    read from both sides: a thread where a reply could be answered with a sign
    its parent could not would make the reader wonder what the difference is.
    What changes is only what the sign is left under.
    """

    comment_id: int
    user_id: int
    reaction: Reaction
    at: datetime
