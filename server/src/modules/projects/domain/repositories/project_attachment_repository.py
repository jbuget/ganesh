"""Port for the files of a mission."""

from abc import ABC, abstractmethod

from src.modules.projects.domain.entities.project_attachment import ProjectAttachment


class ProjectAttachmentRepository(ABC):
    """Persistence contract for what a mission carries besides words."""

    @abstractmethod
    async def get(self, attachment_id: int) -> ProjectAttachment | None: ...

    @abstractmethod
    async def list_for_project(self, project_id: int) -> list[ProjectAttachment]:
        """A mission's files, most recent first."""
        ...

    @abstractmethod
    async def keys_for_project(self, project_id: int) -> list[str]:
        """Where a mission's bytes sit, so a deletion can take them with it."""
        ...

    @abstractmethod
    async def add(self, attachment: ProjectAttachment) -> ProjectAttachment: ...

    @abstractmethod
    async def update(self, attachment: ProjectAttachment) -> ProjectAttachment:
        """Writes back what changed of a file. Only its name ever does."""
        ...

    @abstractmethod
    async def remove(self, attachment_id: int) -> None:
        """Withdraws a file for good. Nothing here is kept as a tombstone: the
        register says who dropped it and who took it away."""
        ...
