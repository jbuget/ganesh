"""Port for the moods the team posts."""

from abc import ABC, abstractmethod
from datetime import date

from src.modules.moods.domain.entities.mood import Mood


class MoodRepository(ABC):
    """Persistence contract for moods."""

    @abstractmethod
    async def get(self, user_id: int, day: date) -> Mood | None: ...

    @abstractmethod
    async def list_between(self, start: date, end: date) -> list[Mood]:
        """Everyone's moods over a window, both ends included."""
        ...

    @abstractmethod
    async def list_for_user_between(
        self, user_id: int, start: date, end: date
    ) -> list[Mood]:
        """One teammate's moods over a window, both ends included."""
        ...

    @abstractmethod
    async def upsert(self, mood: Mood) -> Mood:
        """Writes the mood of a day, or changes the one already posted there."""
        ...
