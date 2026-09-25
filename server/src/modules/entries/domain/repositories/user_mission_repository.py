"""Port for the missions a user put on their month."""

from abc import ABC, abstractmethod
from datetime import date


class UserMissionRepository(ABC):
    """Persistence contract for the rows of a month.

    A row exists as soon as someone puts a mission on their month, before any
    time is entered on it: preparing a month is a gesture of its own, and it
    must survive leaving the screen. What carries time needs no such record —
    an entry already says its mission is there.

    Every method takes any day of the month aimed at: only the month matters,
    and holding it by its first day is the implementation's business.
    """

    @abstractmethod
    async def list_for_month(
        self, user_id: int, month: date
    ) -> list[tuple[int, int | None]]:
        """The rows put on this month, as (mission, activity) pairs.

        The activity is what names a row, so it is part of what identifies
        one: the same mission appears once per trade somebody declares under.
        It is null for off-project work, which is a row on its own.
        """
        ...

    @abstractmethod
    async def add(
        self, user_id: int, project_id: int, activity_id: int | None, month: date
    ) -> None:
        """Puts a row on a month. No effect if it is already there."""
        ...

    @abstractmethod
    async def remove(
        self, user_id: int, project_id: int, activity_id: int | None, month: date
    ) -> None:
        """Takes a row off a month. No effect if it was not there."""
        ...
