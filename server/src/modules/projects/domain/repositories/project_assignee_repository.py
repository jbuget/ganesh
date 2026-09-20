"""Port for the contributors assigned to a mission."""

from abc import ABC, abstractmethod

from src.modules.projects.domain.entities.project_role import ProjectRole


class ProjectAssigneeRepository(ABC):
    """Persistence contract for assignments.

    An assignment says who is working on a mission right now, or is about to.
    It is set by hand and undone the same way: it states a team intention, not
    something deduced from the entries.
    """

    @abstractmethod
    async def list_for_project(self, project_id: int, role: ProjectRole) -> list[int]:
        """Ids of the people holding this role on a mission."""
        ...

    @abstractmethod
    async def list_all(self, role: ProjectRole) -> dict[int, list[int]]:
        """People holding this role on each mission, indexed by mission."""
        ...

    @abstractmethod
    async def list_for_user(self, user_id: int) -> dict[int, list[ProjectRole]]:
        """The missions one person is attached to, and on what grounds.

        The mirror of `list_for_project`: a mission says who works on it, and
        a teammate says what they work on. Both roles come back together —
        the same person often holds both on the same mission.
        """
        ...

    @abstractmethod
    async def assign(self, project_id: int, user_id: int, role: ProjectRole) -> None:
        """Gives someone a role. No effect if they already hold it."""
        ...

    @abstractmethod
    async def unassign(self, project_id: int, user_id: int, role: ProjectRole) -> None:
        """Takes a role away from someone. No effect if they did not hold it."""
        ...
