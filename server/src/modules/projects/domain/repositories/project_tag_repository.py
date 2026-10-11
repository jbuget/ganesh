"""Port for the tags a mission carries."""

from abc import ABC, abstractmethod

from src.modules.projects.domain.entities.tag import Tag


class ProjectTagRepository(ABC):
    """Persistence contract for which mission carries which tag.

    A mission and each of its work packages carry their own: nothing is passed
    down from a project to its packages, nor summed up the other way. A tag is
    put on by hand and taken off the same way, like an assignment.
    """

    @abstractmethod
    async def list_for_project(self, project_id: int) -> list[Tag]:
        """The tags of one mission, in alphabetical order."""
        ...

    @abstractmethod
    async def list_all(self) -> dict[int, list[Tag]]:
        """The tags of every mission at once, indexed by mission.

        The reference list and the board read them by the dozen: asking one
        mission at a time would put the length of the list into the number of
        queries.
        """
        ...

    @abstractmethod
    async def project_ids_for(self, tag_id: int) -> list[int]:
        """The missions carrying a tag."""
        ...

    @abstractmethod
    async def attach(self, project_id: int, tag_id: int) -> None:
        """Puts a tag on a mission. No effect if it already carries it."""
        ...

    @abstractmethod
    async def detach(self, project_id: int, tag_id: int) -> None:
        """Takes a tag off a mission. No effect if it did not carry it."""
        ...
