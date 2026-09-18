"""Port for the collections attached to a mission."""

from abc import ABC, abstractmethod
from datetime import date

from src.modules.projects.domain.entities.project import Department, ProjectStatus
from src.modules.projects.domain.entities.project_link import ProjectLink


class ProjectDetailRepository(ABC):
    """Departments, links and phases reached by a mission.

    These three collections exist only through the project that carries them
    and disappear with it: they belong to the same aggregate, and a single port
    avoids splitting into three what is read and written together.
    """

    @abstractmethod
    async def list_departments(self, project_id: int) -> list[Department]: ...

    @abstractmethod
    async def set_departments(
        self, project_id: int, departments: list[Department]
    ) -> None:
        """Replaces the whole list: the screen sends what it displays."""
        ...

    @abstractmethod
    async def list_links(self, project_id: int) -> list[ProjectLink]: ...

    @abstractmethod
    async def add_link(self, link: ProjectLink) -> ProjectLink: ...

    @abstractmethod
    async def remove_link(self, link_id: int) -> None: ...

    @abstractmethod
    async def list_phases_reached(
        self, project_id: int
    ) -> dict[ProjectStatus, date]: ...

    @abstractmethod
    async def mark_phase_reached(
        self, project_id: int, status: ProjectStatus, reached_at: date
    ) -> None:
        """Records the date a phase was entered. The first one counts."""
        ...
