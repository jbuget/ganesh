"""Port d'acces au referentiel des missions."""

from abc import ABC, abstractmethod

from src.modules.projects.domain.entities.project import Project


class ProjectRepository(ABC):
    """Contrat de persistance des projets, lots et activites hors projet."""

    @abstractmethod
    async def get_by_id(self, project_id: int) -> Project | None: ...

    @abstractmethod
    async def list_all(self, include_inactive: bool = False) -> list[Project]: ...

    @abstractmethod
    async def list_children(self, parent_id: int) -> list[Project]: ...

    @abstractmethod
    async def add(self, project: Project) -> Project: ...

    @abstractmethod
    async def update(self, project: Project) -> Project: ...
