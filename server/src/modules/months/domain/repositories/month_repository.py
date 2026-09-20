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
    async def list_for_user(self, user_id: int, since: date) -> list[Month]:
        """The months one person already has a state for, `since` included.

        A month nobody validated has no row: what comes back describes the
        months that moved, and the caller reads the silence as « open ».
        """
        ...

    @abstractmethod
    async def save(self, month: Month) -> Month: ...
