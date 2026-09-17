"""Port d'acces aux mises a jour d'une mission."""

from abc import ABC, abstractmethod

from src.modules.projects.domain.entities.project_update import ProjectUpdate


class ProjectUpdateRepository(ABC):
    """Contrat de persistance du fil de suivi."""

    @abstractmethod
    async def get(self, update_id: int) -> ProjectUpdate | None: ...

    @abstractmethod
    async def list_for_project(self, project_id: int) -> list[ProjectUpdate]:
        """Le fil d'une mission, de la plus recente a la plus ancienne."""
        ...

    @abstractmethod
    async def count_by_project(self) -> dict[int, int]:
        """Nombre de mises a jour vivantes de chaque mission.

        Les messages retires n'y comptent pas : le tableau annonce ce qui se
        lit encore dans le fil.
        """
        ...

    @abstractmethod
    async def latest_by_project(self) -> dict[int, ProjectUpdate]:
        """Derniere mise a jour encore lisible de chaque mission.

        Une mise a jour retiree laisse la place a celle qui la precede : ce
        qu'on annonce d'un fil, c'est ce qu'on y lirait en l'ouvrant.
        """
        ...

    @abstractmethod
    async def add(self, update: ProjectUpdate) -> ProjectUpdate: ...

    @abstractmethod
    async def update(self, update: ProjectUpdate) -> ProjectUpdate: ...
