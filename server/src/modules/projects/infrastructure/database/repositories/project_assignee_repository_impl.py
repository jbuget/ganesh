"""Persistance des intervenants affectes a une mission."""

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.projects.domain.repositories.project_assignee_repository import (
    ProjectAssigneeRepository,
)
from src.modules.projects.infrastructure.database.models.project_assignee_model import (
    ProjectAssigneeModel,
)


class SqlProjectAssigneeRepository(ProjectAssigneeRepository):
    """Affectations stockees dans la table de liaison."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_project(self, project_id: int, role: ProjectRole) -> list[int]:
        result = await self._session.execute(
            select(ProjectAssigneeModel.user_id).where(
                ProjectAssigneeModel.project_id == project_id,
                ProjectAssigneeModel.role == role,
            )
        )
        return list(result.scalars().all())

    async def list_all(self, role: ProjectRole) -> dict[int, list[int]]:
        """Toutes les affectations d'un coup : le tableau les lit par dizaines."""
        result = await self._session.execute(
            select(ProjectAssigneeModel.project_id, ProjectAssigneeModel.user_id).where(
                ProjectAssigneeModel.role == role
            )
        )
        par_projet: dict[int, list[int]] = {}
        for project_id, user_id in result.all():
            par_projet.setdefault(project_id, []).append(user_id)
        return par_projet

    async def assign(self, project_id: int, user_id: int, role: ProjectRole) -> None:
        # La cle primaire porte les deux colonnes : laisser la base ignorer le
        # doublon evite un aller-retour de verification a chaque clic.
        await self._session.execute(
            insert(ProjectAssigneeModel)
            .values(project_id=project_id, user_id=user_id, role=role)
            .on_conflict_do_nothing()
        )

    async def unassign(self, project_id: int, user_id: int, role: ProjectRole) -> None:
        await self._session.execute(
            delete(ProjectAssigneeModel).where(
                ProjectAssigneeModel.project_id == project_id,
                ProjectAssigneeModel.user_id == user_id,
                ProjectAssigneeModel.role == role,
            )
        )
