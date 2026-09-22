"""Port for the reactions left on a mission's updates."""

from abc import ABC, abstractmethod

from src.modules.projects.domain.entities.update_reaction import (
    Reaction,
    UpdateReaction,
)


class UpdateReactionRepository(ABC):
    """Persistence contract for the signs left under an update."""

    @abstractmethod
    async def list_for_project(
        self, project_id: int
    ) -> dict[int, list[UpdateReaction]]:
        """Every reaction of a mission's thread, by update.

        The thread is read whole: asking update by update would cost one query
        per message for something drawn under every one of them.
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
