"""Port d'acces aux collections attachees a une mission."""

from abc import ABC, abstractmethod
from datetime import date

from src.modules.projects.domain.entities.project import Department, ProjectStatus
from src.modules.projects.domain.entities.project_link import ProjectLink


class ProjectDetailRepository(ABC):
    """Departements, liens et phases atteintes d'une mission.

    Ces trois collections n'existent que par le projet qui les porte et
    disparaissent avec lui : elles relevent du meme agregat, et un port unique
    evite d'eclater en trois ce qui se lit et s'ecrit ensemble.
    """

    @abstractmethod
    async def list_departments(self, project_id: int) -> list[Department]: ...

    @abstractmethod
    async def set_departments(
        self, project_id: int, departments: list[Department]
    ) -> None:
        """Remplace la liste entiere : l'ecran envoie ce qu'il affiche."""
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
        self, project_id: int, statut: ProjectStatus, reached_at: date
    ) -> None:
        """Note la date d'entree dans une phase. La premiere fait foi."""
        ...
