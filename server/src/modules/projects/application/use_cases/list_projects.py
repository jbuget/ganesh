"""Liste le referentiel des missions."""

from dataclasses import dataclass

from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.projects.domain.entities.project import Project
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)


@dataclass
class ListedProject:
    """Une mission et ce que l'interface doit savoir pour proposer ses actions."""

    project: Project
    saisies: int
    sous_projets: int

    @property
    def is_deletable(self) -> bool:
        """Une mission qui n'a jamais servi peut disparaitre ; les autres s'archivent."""
        return self.saisies == 0 and self.sous_projets == 0


class ListProjectsUseCase:
    """Retourne les missions, actives par defaut."""

    def __init__(self, projects: ProjectRepository, entries: EntryRepository) -> None:
        self._projects = projects
        self._entries = entries

    async def execute(self, include_inactive: bool = False) -> list[ListedProject]:
        missions = await self._projects.list_all(include_inactive=include_inactive)
        saisies = await self._entries.count_by_project()

        enfants: dict[int, int] = {}
        for mission in await self._projects.list_all(include_inactive=True):
            if mission.parent_id is not None:
                enfants[mission.parent_id] = enfants.get(mission.parent_id, 0) + 1

        return [
            ListedProject(
                project=mission,
                saisies=saisies.get(mission.id or 0, 0),
                sous_projets=enfants.get(mission.id or 0, 0),
            )
            for mission in missions
        ]
