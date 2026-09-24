"""Access to the activities a mission is cut into."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from src.modules.projects.domain.entities.activity import Activity


class ActivityRepository(ABC):
    """Reads and writes the activities days are booked against."""

    @abstractmethod
    async def add(self, activity: Activity) -> Activity: ...

    @abstractmethod
    async def get_by_id(self, activity_id: int) -> Activity | None: ...

    @abstractmethod
    async def update(self, activity: Activity) -> Activity: ...

    @abstractmethod
    async def list_for_project(self, project_id: int) -> list[Activity]:
        """The activities of one mission, active ones first read as given."""
        ...

    @abstractmethod
    async def list_for_projects(
        self, project_ids: Sequence[int]
    ) -> dict[int, list[Activity]]:
        """The activities of several missions, in one query whatever the count.

        A screen listing the reference list needs every mission's activities
        at once; asking for them one mission at a time would put the count of
        the list into the count of the queries.
        """
        ...

    @abstractmethod
    async def count_entries(self, activity_id: int) -> int:
        """How many days are booked against it.

        What a screen has to say before withdrawing one: an activity nobody
        declared on leaves quietly, one that carries a year of days does not.
        """
        ...
