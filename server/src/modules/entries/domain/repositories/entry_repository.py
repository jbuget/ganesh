"""Port for time entries."""

from abc import ABC, abstractmethod
from datetime import date

from src.modules.entries.domain.entities.entry import Entry


class EntryRepository(ABC):
    """Persistence contract for entries."""

    @abstractmethod
    async def get(self, user_id: int, project_id: int, day: date) -> Entry | None: ...

    @abstractmethod
    async def list_for_month(self, user_id: int, month: date) -> list[Entry]: ...

    @abstractmethod
    async def list_for_day(self, user_id: int, day: date) -> list[Entry]: ...

    @abstractmethod
    async def list_for_project(self, project_id: int) -> list[Entry]: ...

    @abstractmethod
    async def count_by_project(self) -> dict[int, int]:
        """Entry count per mission, to know which ones have been used."""
        ...

    @abstractmethod
    async def sum_realised_by_project(self, today: date) -> dict[int, float]:
        """Delivered days per mission: forecasts do not count.

        Summed in one go: the reference list lines up dozens of missions, and
        one query per row would make them arrive one after the other.
        """
        ...

    @abstractmethod
    async def upsert(self, entry: Entry) -> Entry: ...

    @abstractmethod
    async def delete(self, user_id: int, project_id: int, day: date) -> None: ...
