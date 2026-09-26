"""Access to the dates a mission answers for."""

from abc import ABC, abstractmethod

from src.modules.projects.domain.entities.milestone import Milestone


class MilestoneRepository(ABC):
    """Reads and writes the milestones posted on a mission."""

    @abstractmethod
    async def add(self, milestone: Milestone) -> Milestone: ...

    @abstractmethod
    async def get_by_id(self, milestone_id: int) -> Milestone | None: ...

    @abstractmethod
    async def update(self, milestone: Milestone) -> Milestone: ...

    @abstractmethod
    async def list_for_project(self, project_id: int) -> list[Milestone]:
        """The milestones of one mission, in the order they happen.

        A list of dates reads as a timeline: sorted by the day announced, so
        that what is next is read next, whether or not it has been reached.
        """
        ...

    @abstractmethod
    async def delete(self, milestone_id: int) -> None:
        """Removes a milestone for good.

        No archiving here, unlike an activity: nothing is ever booked against
        a date, so its going empties no month and loses no declared day.
        """
        ...
