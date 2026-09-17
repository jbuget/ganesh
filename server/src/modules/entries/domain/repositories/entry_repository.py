"""Port d'acces aux saisies de temps."""

from abc import ABC, abstractmethod
from datetime import date

from src.modules.entries.domain.entities.entry import Entry


class EntryRepository(ABC):
    """Contrat de persistance des saisies."""

    @abstractmethod
    async def get(self, user_id: int, project_id: int, jour: date) -> Entry | None: ...

    @abstractmethod
    async def list_for_month(self, user_id: int, mois: date) -> list[Entry]: ...

    @abstractmethod
    async def list_for_day(self, user_id: int, jour: date) -> list[Entry]: ...

    @abstractmethod
    async def list_for_project(self, project_id: int) -> list[Entry]: ...

    @abstractmethod
    async def count_by_project(self) -> dict[int, int]:
        """Nombre de saisies par mission, pour savoir lesquelles ont servi."""
        ...

    @abstractmethod
    async def sum_realised_by_project(self, today: date) -> dict[int, float]:
        """Jours realises par mission : le previsionnel n'y entre pas.

        Somme lue en une fois : le referentiel aligne des dizaines de missions,
        et une requete par ligne les ferait arriver l'une apres l'autre.
        """
        ...

    @abstractmethod
    async def upsert(self, entry: Entry) -> Entry: ...

    @abstractmethod
    async def delete(self, user_id: int, project_id: int, jour: date) -> None: ...
