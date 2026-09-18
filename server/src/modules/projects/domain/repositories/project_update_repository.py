"""Port for the updates of a mission."""

from abc import ABC, abstractmethod

from src.modules.projects.domain.entities.project_update import ProjectUpdate


class ProjectUpdateRepository(ABC):
    """Persistence contract for the follow-up thread."""

    @abstractmethod
    async def get(self, update_id: int) -> ProjectUpdate | None: ...

    @abstractmethod
    async def list_for_project(self, project_id: int) -> list[ProjectUpdate]:
        """A mission's thread, from the most recent to the oldest."""
        ...

    @abstractmethod
    async def count_by_project(self) -> dict[int, int]:
        """How many live updates each mission has.

        Withdrawn messages do not count: the board announces what can still be
        read in the thread.
        """
        ...

    @abstractmethod
    async def latest_by_project(self) -> dict[int, ProjectUpdate]:
        """The latest still-readable update of each mission.

        A withdrawn update gives way to the one before it: what a thread
        announces is what one would read on opening it.
        """
        ...

    @abstractmethod
    async def add(self, update: ProjectUpdate) -> ProjectUpdate: ...

    @abstractmethod
    async def update(self, update: ProjectUpdate) -> ProjectUpdate: ...
