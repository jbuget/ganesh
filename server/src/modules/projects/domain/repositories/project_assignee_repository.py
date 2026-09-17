"""Port d'acces aux intervenants affectes a une mission."""

from abc import ABC, abstractmethod


class ProjectAssigneeRepository(ABC):
    """Contrat de persistance des affectations.

    Une affectation dit qui intervient sur une mission en ce moment, ou doit
    s'y mettre sous peu. Elle est posee a la main et se defait de meme : c'est
    une intention d'equipe, pas une deduction faite depuis les saisies.
    """

    @abstractmethod
    async def list_for_project(self, project_id: int) -> list[int]:
        """Identifiants des intervenants d'une mission."""
        ...

    @abstractmethod
    async def list_all(self) -> dict[int, list[int]]:
        """Intervenants de toutes les missions, indexes par mission."""
        ...

    @abstractmethod
    async def assign(self, project_id: int, user_id: int) -> None:
        """Ajoute un intervenant. Sans effet s'il y est deja."""
        ...

    @abstractmethod
    async def unassign(self, project_id: int, user_id: int) -> None:
        """Retire un intervenant. Sans effet s'il n'y etait pas."""
        ...
