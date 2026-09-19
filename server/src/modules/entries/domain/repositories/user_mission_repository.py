"""Port for the missions a user put on their month."""

from abc import ABC, abstractmethod
from datetime import date


class UserMissionRepository(ABC):
    """Persistence contract for the rows of a month.

    A row exists as soon as someone puts a mission on their month, before any
    time is entered on it: preparing a month is a gesture of its own, and it
    must survive leaving the screen. What carries time needs no such record —
    an entry already says its mission is there.
    """

    @abstractmethod
    async def list_for_month(self, user_id: int, month: date) -> list[int]:
        """Ids of the missions put on this month."""
        ...

    @abstractmethod
    async def add(self, user_id: int, project_id: int, month: date) -> None:
        """Puts a mission on a month. No effect if it is already there."""
        ...

    @abstractmethod
    async def remove(self, user_id: int, project_id: int, month: date) -> None:
        """Takes a mission off a month. No effect if it was not there."""
        ...
