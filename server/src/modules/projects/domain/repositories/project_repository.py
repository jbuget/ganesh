"""Port for the mission reference list."""

from abc import ABC, abstractmethod

from src.modules.projects.domain.entities.project import Project


class ProjectRepository(ABC):
    """Persistence contract for projects, work packages and off-project work."""

    @abstractmethod
    async def get_by_id(self, project_id: int) -> Project | None: ...

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Project | None:
        """The mission a public address points at, if any claims it."""
        ...

    @abstractmethod
    async def list_all(self, include_inactive: bool = False) -> list[Project]: ...

    @abstractmethod
    async def list_children(self, parent_id: int) -> list[Project]: ...

    @abstractmethod
    async def add(self, project: Project) -> Project: ...

    @abstractmethod
    async def update(self, project: Project) -> Project: ...

    @abstractmethod
    async def delete(self, project_id: int) -> None: ...
