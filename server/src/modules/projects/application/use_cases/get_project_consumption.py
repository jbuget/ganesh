"""What a project has cost, trade by trade, lots included."""

from dataclasses import dataclass, field
from datetime import date

from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.projects.domain.entities.project import Project
from src.modules.projects.domain.repositories.activity_repository import (
    ActivityRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.services.consumption import TradeConsumption, by_trade
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from src.shared.utils import clock


@dataclass
class ProjectConsumption:
    """A project and its trades, then its work packages and theirs.

    It stops one level down: a work package carries activities and never
    another package.
    """

    project: Project
    trades: list[TradeConsumption]
    work_packages: list["ProjectConsumption"] = field(default_factory=list)


class GetProjectConsumptionUseCase:
    """Reads what each trade of a project, and of its lots, has cost."""

    def __init__(
        self,
        projects: ProjectRepository,
        activities: ActivityRepository,
        entries: EntryRepository,
    ) -> None:
        self._projects = projects
        self._activities = activities
        self._entries = entries

    async def execute(
        self, project_id: int, today: date | None = None
    ) -> ProjectConsumption:
        project = await self._projects.get_by_id(project_id)
        if project is None:
            raise EntityNotFoundError("The mission cannot be found.")

        day = today or clock.today()
        lots = await self._projects.list_children(project_id)
        return ProjectConsumption(
            project=project,
            trades=await self._read(project_id, day),
            work_packages=[
                ProjectConsumption(
                    project=lot, trades=await self._read(lot.id or 0, day)
                )
                for lot in sorted(lots, key=lambda lot: lot.label.lower())
            ],
        )

    async def _read(self, project_id: int, today: date) -> list[TradeConsumption]:
        activities = await self._activities.list_for_project(project_id)
        entries = await self._entries.list_for_project(project_id)
        return by_trade(
            activities,
            [(entry.activity_id, entry.day, float(entry.value)) for entry in entries],
            today,
        )
