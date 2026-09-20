"""Handing the register over for a window, in one go.

The grid answers one person's question — my month — and the screen is built
around it. An export answers a different one: what the whole team declared,
between two days, on whatever mission. Looping over grids to get there would
make the caller redo the join this does once, N people by M months.
"""

from dataclasses import dataclass
from datetime import date

from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.projects.domain.entities.project import ProjectStatus
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import ValidationError

#: A year and a day. Not a business rule — a guard on a route a machine calls,
#: so that one mistyped date does not ask for the whole history at once. A
#: caller that wants more asks twice, which is what paging would have made it
#: do anyway.
MAX_EXPORT_DAYS = 366


@dataclass(frozen=True)
class ExportedEntry:
    """One declared day, carrying the names a reader needs to make sense of it.

    The labels travel beside the ids on purpose. An export is read once, by
    something that has no other way of asking who user 14 is, and the ids stay
    so that a second pull can be reconciled with the first.
    """

    day: date
    value: float
    status_at_entry: ProjectStatus | None
    user_id: int
    user_label: str
    project_id: int
    project_label: str


class ExportEntriesUseCase:
    """Every entry of a window, named."""

    def __init__(
        self,
        entries: EntryRepository,
        users: UserRepository,
        projects: ProjectRepository,
    ) -> None:
        self._entries = entries
        self._users = users
        self._projects = projects

    async def execute(self, start: date, end: date) -> list[ExportedEntry]:
        if end < start:
            raise ValidationError("The window ends before it starts.")
        if (end - start).days + 1 > MAX_EXPORT_DAYS:
            raise ValidationError(
                f"An export covers at most {MAX_EXPORT_DAYS} days at a time."
            )

        entries = await self._entries.list_over(start, end)
        # Deactivated teammates and archived missions are read too: they are
        # what the window holds, and an export that dropped them would not add
        # up to what the month it covers was.
        people = {
            person.id: person.label
            for person in await self._users.list_all(include_inactive=True)
        }
        missions = {
            mission.id: mission.label
            for mission in await self._projects.list_all(include_inactive=True)
        }
        return [
            ExportedEntry(
                day=entry.day,
                value=float(entry.value),
                status_at_entry=entry.status_at_entry,
                user_id=entry.user_id,
                user_label=people.get(entry.user_id, ""),
                project_id=entry.project_id,
                project_label=missions.get(entry.project_id, ""),
            )
            for entry in entries
        ]
