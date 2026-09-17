"""Persistance des collections attachees a une mission."""

from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.projects.domain.entities.project import Department, ProjectStatus
from src.modules.projects.domain.entities.project_link import ProjectLink
from src.modules.projects.domain.repositories.project_detail_repository import (
    ProjectDetailRepository,
)
from src.modules.projects.infrastructure.database.models.project_detail_models import (
    ProjectDepartmentModel,
    ProjectLinkModel,
    ProjectPhaseReachedModel,
)


class SqlProjectDetailRepository(ProjectDetailRepository):
    """Collections du detail, en base."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_departments(self, project_id: int) -> list[Department]:
        result = await self._session.execute(
            select(ProjectDepartmentModel.department).where(
                ProjectDepartmentModel.project_id == project_id
            )
        )
        return list(result.scalars().all())

    async def set_departments(
        self, project_id: int, departments: list[Department]
    ) -> None:
        await self._session.execute(
            delete(ProjectDepartmentModel).where(
                ProjectDepartmentModel.project_id == project_id
            )
        )
        for department in dict.fromkeys(departments):
            await self._session.execute(
                insert(ProjectDepartmentModel).values(
                    project_id=project_id, department=department
                )
            )

    async def list_links(self, project_id: int) -> list[ProjectLink]:
        result = await self._session.execute(
            select(ProjectLinkModel)
            .where(ProjectLinkModel.project_id == project_id)
            .order_by(ProjectLinkModel.id)
        )
        return [
            ProjectLink(
                id=row.id,
                project_id=row.project_id,
                label=row.label,
                url=row.url,
                icone=row.icone,
            )
            for row in result.scalars().all()
        ]

    async def add_link(self, link: ProjectLink) -> ProjectLink:
        model = ProjectLinkModel(
            project_id=link.project_id,
            label=link.label,
            url=link.url,
            icone=link.icone,
        )
        self._session.add(model)
        await self._session.flush()
        link.id = model.id
        return link

    async def remove_link(self, link_id: int) -> None:
        await self._session.execute(
            delete(ProjectLinkModel).where(ProjectLinkModel.id == link_id)
        )

    async def list_phases_reached(self, project_id: int) -> dict[ProjectStatus, date]:
        result = await self._session.execute(
            select(
                ProjectPhaseReachedModel.statut, ProjectPhaseReachedModel.reached_at
            ).where(ProjectPhaseReachedModel.project_id == project_id)
        )
        return dict(result.all())  # type: ignore[arg-type]

    async def mark_phase_reached(
        self, project_id: int, statut: ProjectStatus, reached_at: date
    ) -> None:
        # La premiere date fait foi : repasser par une phase ne reecrit pas
        # l'histoire, et l'on garde la date du premier franchissement.
        await self._session.execute(
            insert(ProjectPhaseReachedModel)
            .values(project_id=project_id, statut=statut, reached_at=reached_at)
            .on_conflict_do_nothing()
        )
