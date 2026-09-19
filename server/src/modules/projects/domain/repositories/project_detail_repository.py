"""Port for the collections attached to a mission."""

from abc import ABC, abstractmethod
from datetime import date

from src.modules.projects.domain.entities.project import ProjectStatus
from src.modules.projects.domain.entities.project_link import ProjectLink
from src.shared.enums.department import Department


class ProjectDetailRepository(ABC):
    """The collections hanging off a mission.

    Departments, links and phases reached, plus what the service catalogue
    adds: stack, tags and dependencies. They all exist only through the project
    that carries them and disappear with it — they belong to the same
    aggregate, and a single port avoids splitting what is read together.
    """

    @abstractmethod
    async def list_departments(self, project_id: int) -> list[Department]:
        """The departments of one mission, in the order `Department` declares.

        That is the order the picker offers them in, and the order the
        reference list reads them in: nothing says in which order they were
        stored, so a mission read as it comes would show its chips one way in
        its panel and another in the column — and move them about from one
        load to the next.
        """
        ...

    @abstractmethod
    async def list_departments_by_project(self) -> dict[int, list[Department]]:
        """The departments of every mission, read in one go.

        The reference list shows them in a column: asking for them mission by
        mission would make the rows arrive one after the other. Same order as
        above, for the same reason.
        """
        ...

    @abstractmethod
    async def set_departments(
        self, project_id: int, departments: list[Department]
    ) -> None:
        """Replaces the whole list: the screen sends what it displays."""
        ...

    @abstractmethod
    async def list_links(self, project_id: int) -> list[ProjectLink]: ...

    @abstractmethod
    async def list_links_by_project(self) -> dict[int, list[ProjectLink]]:
        """The links of every mission, read in one go.

        The reference list shows them in a column: asking for them mission by
        mission would make the rows arrive one after the other.
        """
        ...

    @abstractmethod
    async def add_link(self, link: ProjectLink) -> ProjectLink: ...

    @abstractmethod
    async def remove_link(self, link_id: int) -> None: ...

    @abstractmethod
    async def list_phases_reached(
        self, project_id: int
    ) -> dict[ProjectStatus, date]: ...

    @abstractmethod
    async def list_phases_reached_by_project(
        self,
    ) -> dict[int, dict[ProjectStatus, date]]:
        """The whole phase history of every mission, read in one go.

        A roadmap draws every bar on one screen, and each bar is made of the
        phases its mission crossed: asking for them mission by mission would
        turn one drawing into fifty queries.
        """
        ...

    @abstractmethod
    async def list_dates_reached(self, status: ProjectStatus) -> dict[int, date]:
        """The day each mission entered a phase, read in one go.

        The reference list lines up dozens of missions: asking for their
        history one by one would make them arrive one after the other.
        """
        ...

    @abstractmethod
    async def mark_phase_reached(
        self, project_id: int, status: ProjectStatus, reached_at: date
    ) -> None:
        """Records the date a phase was entered. The first one counts."""
        ...

    @abstractmethod
    async def list_stack(self, project_id: int) -> list[str]: ...

    @abstractmethod
    async def set_stack(self, project_id: int, technologies: list[str]) -> None:
        """Replaces the whole list: the screen sends what it displays."""
        ...

    @abstractmethod
    async def list_tags(self, project_id: int) -> list[str]: ...

    @abstractmethod
    async def set_tags(self, project_id: int, tags: list[str]) -> None:
        """Replaces the whole list: the screen sends what it displays."""
        ...

    @abstractmethod
    async def list_dependencies(self, project_id: int) -> list[int]: ...

    @abstractmethod
    async def set_dependencies(self, project_id: int, depends_on: list[int]) -> None:
        """Replaces the whole list: the screen sends what it displays."""
        ...
