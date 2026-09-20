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
    async def authors_for_project(self, project_id: int) -> set[int]:
        """Who has already posted in a mission's thread.

        Having spoken in a thread is reason enough to hear the answer:
        one asks a question on a neighbouring mission without being
        declared on it, and would otherwise never know it was answered.
        A withdrawn message still counts — its author was there.
        """
        ...

    @abstractmethod
    async def add(self, update: ProjectUpdate) -> ProjectUpdate: ...

    @abstractmethod
    async def update(self, update: ProjectUpdate) -> ProjectUpdate: ...
