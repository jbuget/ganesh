"""Port for the replies written under a mission's updates."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from src.modules.projects.domain.entities.update_comment import UpdateComment


class UpdateCommentRepository(ABC):
    """Persistence contract for what hangs under an update."""

    @abstractmethod
    async def get(self, comment_id: int) -> UpdateComment | None: ...

    @abstractmethod
    async def list_for_updates(
        self, update_ids: Sequence[int]
    ) -> dict[int, list[UpdateComment]]:
        """The replies written under these updates, oldest first.

        Forward, where the thread itself runs backwards: one opens a thread to
        see what is new and reads a conversation from its beginning.

        They are asked for together, as the reactions are: a thread of twenty
        updates would otherwise cost twenty queries to draw once.
        """
        ...

    @abstractmethod
    async def list_for_project(self, project_id: int) -> list[UpdateComment]:
        """Every reply written anywhere in a mission's thread.

        What it is for is counting the files a thread shows: an image pasted
        into a reply leaves the same hole when the file goes as one pasted
        into an update.
        """
        ...

    @abstractmethod
    async def authors_for_update(self, update_id: int) -> list[int]:
        """Who has already answered under an update, in the order they came.

        Having answered is what puts somebody in the conversation: they hear
        the next reply without being on the mission, and without having been
        named. A withdrawn reply still counts — its author was there.
        """
        ...

    @abstractmethod
    async def add(self, comment: UpdateComment) -> UpdateComment: ...

    @abstractmethod
    async def update(self, comment: UpdateComment) -> UpdateComment: ...
