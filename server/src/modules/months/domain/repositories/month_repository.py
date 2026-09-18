"""Port for the entry state of months."""

from abc import ABC, abstractmethod
from datetime import date

from src.modules.months.domain.entities.month import Month


class MonthRepository(ABC):
    """Persistence contract for month state."""

    @abstractmethod
    async def get(self, user_id: int, month: date) -> Month | None: ...

    @abstractmethod
    async def list_for_month(self, month: date) -> list[Month]: ...

    @abstractmethod
    async def save(self, month: Month) -> Month: ...
