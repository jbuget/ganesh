"""Port d'acces aux intervenants affectes a une mission."""

from abc import ABC, abstractmethod

from src.modules.projects.domain.entities.project_role import ProjectRole


class ProjectAssigneeRepository(ABC):
    """Contrat de persistance des affectations.

    Une affectation dit qui intervient sur une mission en ce moment, ou doit
    s'y mettre sous peu. Elle est posee a la main et se defait de meme : c'est
    une intention d'equipe, pas une deduction faite depuis les saisies.
    """

    @abstractmethod
    async def list_for_project(self, project_id: int, role: ProjectRole) -> list[int]:
        """Identifiants des personnes tenant ce role sur une mission."""
        ...

    @abstractmethod
    async def list_all(self, role: ProjectRole) -> dict[int, list[int]]:
        """Personnes tenant ce role sur chaque mission, indexees par mission."""
        ...

    @abstractmethod
    async def assign(self, project_id: int, user_id: int, role: ProjectRole) -> None:
        """Confie un role a quelqu'un. Sans effet s'il le tient deja."""
        ...

    @abstractmethod
    async def unassign(self, project_id: int, user_id: int, role: ProjectRole) -> None:
        """Retire un role a quelqu'un. Sans effet s'il ne le tenait pas."""
        ...
