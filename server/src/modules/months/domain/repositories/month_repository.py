"""Port d'acces a l'etat de saisie des mois."""

from abc import ABC, abstractmethod
from datetime import date

from src.modules.months.domain.entities.month import Month


class MonthRepository(ABC):
    """Contrat de persistance de l'etat des mois."""

    @abstractmethod
    async def get(self, user_id: int, mois: date) -> Month | None: ...

    @abstractmethod
    async def list_for_month(self, mois: date) -> list[Month]: ...

    @abstractmethod
    async def save(self, month: Month) -> Month: ...
