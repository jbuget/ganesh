"""Port for time entries."""

from abc import ABC, abstractmethod
from datetime import date

from src.modules.entries.domain.entities.entry import Entry
from src.modules.projects.domain.entities.project import ProjectStatus


class EntryRepository(ABC):
    """Persistence contract for entries."""

    @abstractmethod
    async def get(
        self, user_id: int, project_id: int, activity_id: int | None, day: date
    ) -> Entry | None:
        """One slot of the grid. The activity is part of what names it: the
        same person may declare on the same mission the same day under two
        trades, and those are two entries, not one overwriting the other."""
        ...

    @abstractmethod
    async def list_for_month(self, user_id: int, month: date) -> list[Entry]: ...

    @abstractmethod
    async def list_for_day(self, user_id: int, day: date) -> list[Entry]: ...

    @abstractmethod
    async def list_for_user_between(
        self, user_id: int, start: date, end: date
    ) -> list[Entry]:
        """Everything one person declared over a window, day by day.

        The entries themselves rather than sums: what is read from them —
        days per mission, the filling of each month, delivered told from
        forecast — is the domain's business, and a port that answered each of
        those questions on its own would state the same window three times.
        """
        ...

    @abstractmethod
    async def list_for_project(self, project_id: int) -> list[Entry]: ...

    @abstractmethod
    async def count_by_project(self) -> dict[int, int]:
        """Entry count per mission, to know which ones have been used."""
        ...

    @abstractmethod
    async def sum_realised_by_project(self, today: date) -> dict[int, float]:
        """Delivered days per mission: forecasts do not count.

        Summed in one go: the reference list lines up dozens of missions, and
        one query per row would make them arrive one after the other.
        """
        ...

    @abstractmethod
    async def sum_realised_by_project_and_status(
        self, today: date, since: date | None = None
    ) -> dict[int, dict[ProjectStatus | None, float]]:
        """Delivered days per mission, kept apart by the phase they were spent in.

        The phase each entry carries is raw data, not a reading: telling build
        from run is the domain's business, and this port only hands over the
        sums. `since` narrows the window, which is how a recent pace is read.
        """
        ...

    @abstractmethod
    async def span_by_project(self) -> dict[int, tuple[date, date]]:
        """The first and the last day declared on each mission.

        What a roadmap opens a bar on when the phase history says nothing:
        a mission somebody spent forty days on before the reference list
        recorded a single transition still has a past, and it starts there.

        Forecasts count. A day posted ahead is part of the mission's span:
        the bar it draws is cut at today by whoever draws it, not here.
        """
        ...

    @abstractmethod
    async def sum_forecast_by_project(self, today: date) -> dict[int, float]:
        """Days already posted ahead on each mission: delivered ones do not count.

        A forecast entered by hand is a piece of the plan already made. A
        projection must take it off what is left to place, or it would plan
        the same days twice.
        """
        ...

    @abstractmethod
    async def sum_by_user_and_day(
        self, start: date, end: date
    ) -> dict[int, dict[date, float]]:
        """What each person has declared on each day of a window.

        Delivered and forecast alike: what a projection needs to know is not
        which of the two a day holds, but whether it still has any room.
        """
        ...

    @abstractmethod
    async def list_over(self, start: date, end: date) -> list[Entry]:
        """Every entry of a window, whoever declared it, on whatever mission.

        What an export reads. The other listings answer one person's question
        — my month, my day — and looping over them to build a register would
        make the caller do the join this does once.
        """
        ...

    @abstractmethod
    async def upsert(self, entry: Entry) -> Entry: ...

    @abstractmethod
    async def delete(
        self, user_id: int, project_id: int, activity_id: int | None, day: date
    ) -> None: ...
