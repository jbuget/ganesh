"""Liste le referentiel des missions."""

from src.modules.projects.domain.entities.project import Project
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)


class ListProjectsUseCase:
    """Retourne les missions, actives par defaut."""

    def __init__(self, projects: ProjectRepository) -> None:
        self._projects = projects

    async def execute(self, include_inactive: bool = False) -> list[Project]:
        return await self._projects.list_all(include_inactive=include_inactive)
