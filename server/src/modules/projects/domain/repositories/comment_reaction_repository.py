"""Port for the reactions left on the replies of a thread."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from src.modules.projects.domain.entities.comment_reaction import CommentReaction
from src.modules.projects.domain.entities.update_reaction import Reaction


class CommentReactionRepository(ABC):
    """Persistence contract for the signs left under a comment."""

    @abstractmethod
    async def list_for_comments(
        self, comment_ids: Sequence[int]
    ) -> dict[int, list[CommentReaction]]:
        """The reactions left on these comments, by comment.

        Asked for together, as an update's are: a sign is drawn under every
        reply of the thread, and asking one by one would cost a query a line.
        """
        ...

    @abstractmethod
    async def add(self, reaction: CommentReaction) -> None:
        """Leaves a sign. Leaving the same one twice changes nothing."""
        ...

    @abstractmethod
    async def remove(self, comment_id: int, user_id: int, reaction: Reaction) -> None:
        """Takes a sign back. Taking back one never left changes nothing."""
        ...
