"""Port for the rhythms teammates declare."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from src.modules.users.domain.entities.rhythm import Rhythm, RhythmHistory


class RhythmRepository(ABC):
    """Persistence contract for declared rhythms."""

    @abstractmethod
    async def history_of(self, user_id: int) -> RhythmHistory: ...

    @abstractmethod
    async def histories_of(self, user_ids: Sequence[int]) -> dict[int, RhythmHistory]:
        """Everyone's history at once.

        A screen reading a window over the whole team asks for the lot: a
        coverage computed thirty queries at a time is the same figure, read
        thirty times slower.
        """

    @abstractmethod
    async def declare(self, rhythm: Rhythm) -> Rhythm:
        """Writes down a rhythm, replacing one already opening that same day.

        Declaring twice on one date is a correction, not a second rhythm:
        what the register holds is what a day expects, and a day expects one
        thing.
        """
