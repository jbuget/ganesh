"""Port for the reactions left on a mission's updates."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from src.modules.projects.domain.entities.update_reaction import (
    Reaction,
    UpdateReaction,
)


class UpdateReactionRepository(ABC):
    """Persistence contract for the signs left under an update."""

    @abstractmethod
    async def list_for_updates(
        self, update_ids: Sequence[int]
    ) -> dict[int, list[UpdateReaction]]:
        """The reactions left on these updates, by update.

        The updates are named rather than their mission: which update belongs
        to which mission is the thread's business, and a store that had to
        answer that would be reading a table it does not own. The caller holds
        the thread already.

        They are asked for together: a reaction is drawn under every message,
        and asking one by one would cost a query per line.
        """
        ...

    @abstractmethod
    async def add(self, reaction: UpdateReaction) -> None:
        """Leaves a sign. Leaving the same one twice changes nothing."""
        ...

    @abstractmethod
    async def remove(self, update_id: int, user_id: int, reaction: Reaction) -> None:
        """Takes a sign back. Taking back one never left changes nothing."""
        ...
