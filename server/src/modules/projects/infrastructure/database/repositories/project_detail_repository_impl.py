"""Persistence of the collections attached to a mission."""

from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.projects.domain.entities.project import ProjectStatus
from src.modules.projects.domain.entities.project_link import ProjectLink
from src.modules.projects.domain.repositories.project_detail_repository import (
    ProjectDetailRepository,
)
from src.modules.projects.infrastructure.database.models.project_detail_models import (
    ProjectDepartmentModel,
    ProjectDependencyModel,
    ProjectLinkModel,
    ProjectPhaseReachedModel,
    ProjectStackModel,
    ProjectTagModel,
)
from src.shared.enums.department import Department, in_declared_order


class SqlProjectDetailRepository(ProjectDetailRepository):
    """Detail collections, in the database."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_departments(self, project_id: int) -> list[Department]:
        result = await self._session.execute(
            select(ProjectDepartmentModel.department).where(
                ProjectDepartmentModel.project_id == project_id
            )
        )
        return in_declared_order(list(result.scalars().all()))

    async def list_departments_by_project(self) -> dict[int, list[Department]]:
        result = await self._session.execute(
            select(ProjectDepartmentModel.project_id, ProjectDepartmentModel.department)
        )
        by_project: dict[int, list[Department]] = {}
        for project_id, department in result.all():
            by_project.setdefault(project_id, []).append(department)
        return {
            project_id: in_declared_order(departments)
            for project_id, departments in by_project.items()
        }

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
                icon=row.icon,
            )
            for row in result.scalars().all()
        ]

    async def list_links_by_project(self) -> dict[int, list[ProjectLink]]:
        result = await self._session.execute(
            select(ProjectLinkModel).order_by(
                ProjectLinkModel.project_id, ProjectLinkModel.id
            )
        )
        by_project: dict[int, list[ProjectLink]] = {}
        for row in result.scalars().all():
            by_project.setdefault(row.project_id, []).append(
                ProjectLink(
                    id=row.id,
                    project_id=row.project_id,
                    label=row.label,
                    url=row.url,
                    icon=row.icon,
                )
            )
        return by_project

    async def add_link(self, link: ProjectLink) -> ProjectLink:
        model = ProjectLinkModel(
            project_id=link.project_id,
            label=link.label,
            url=link.url,
            icon=link.icon,
        )
        self._session.add(model)
        await self._session.flush()
        link.id = model.id
        return link

    async def get_link(self, link_id: int) -> ProjectLink | None:
        row = await self._session.get(ProjectLinkModel, link_id)
        if row is None:
            return None
        return ProjectLink(
            id=row.id,
            project_id=row.project_id,
            label=row.label,
            url=row.url,
            icon=row.icon,
        )

    async def remove_link(self, link_id: int) -> None:
        await self._session.execute(
            delete(ProjectLinkModel).where(ProjectLinkModel.id == link_id)
        )

    async def list_phases_reached(self, project_id: int) -> dict[ProjectStatus, date]:
        result = await self._session.execute(
            select(
                ProjectPhaseReachedModel.status, ProjectPhaseReachedModel.reached_at
            ).where(ProjectPhaseReachedModel.project_id == project_id)
        )
        return dict(result.all())  # type: ignore[arg-type]

    async def list_phases_reached_by_project(
        self,
    ) -> dict[int, dict[ProjectStatus, date]]:
        result = await self._session.execute(
            select(
                ProjectPhaseReachedModel.project_id,
                ProjectPhaseReachedModel.status,
                ProjectPhaseReachedModel.reached_at,
            )
        )
        history: dict[int, dict[ProjectStatus, date]] = {}
        for project_id, status, reached_at in result.all():
            history.setdefault(project_id, {})[status] = reached_at
        return history

    async def list_dates_reached(self, status: ProjectStatus) -> dict[int, date]:
        result = await self._session.execute(
            select(
                ProjectPhaseReachedModel.project_id,
                ProjectPhaseReachedModel.reached_at,
            ).where(ProjectPhaseReachedModel.status == status)
        )
        return dict(result.all())  # type: ignore[arg-type]

    async def mark_phase_reached(
        self, project_id: int, status: ProjectStatus, reached_at: date
    ) -> None:
        # The first date is the one that counts: passing through a phase again
        # does not rewrite history, and the first crossing is kept.
        await self._session.execute(
            insert(ProjectPhaseReachedModel)
            .values(project_id=project_id, status=status, reached_at=reached_at)
            .on_conflict_do_nothing()
        )

    # --- Service catalogue --------------------------------------------------
    # Three lists of the same shape: read sorted so the sheet does not reorder
    # itself between two visits, and rewritten whole, as the departments are.

    async def list_stack(self, project_id: int) -> list[str]:
        result = await self._session.execute(
            select(ProjectStackModel.technology)
            .where(ProjectStackModel.project_id == project_id)
            .order_by(ProjectStackModel.technology)
        )
        return list(result.scalars().all())

    async def set_stack(self, project_id: int, technologies: list[str]) -> None:
        await self._session.execute(
            delete(ProjectStackModel).where(ProjectStackModel.project_id == project_id)
        )
        for technology in dict.fromkeys(technologies):
            await self._session.execute(
                insert(ProjectStackModel).values(
                    project_id=project_id, technology=technology
                )
            )

    async def list_tags(self, project_id: int) -> list[str]:
        result = await self._session.execute(
            select(ProjectTagModel.tag)
            .where(ProjectTagModel.project_id == project_id)
            .order_by(ProjectTagModel.tag)
        )
        return list(result.scalars().all())

    async def set_tags(self, project_id: int, tags: list[str]) -> None:
        await self._session.execute(
            delete(ProjectTagModel).where(ProjectTagModel.project_id == project_id)
        )
        for tag in dict.fromkeys(tags):
            await self._session.execute(
                insert(ProjectTagModel).values(project_id=project_id, tag=tag)
            )

    async def list_dependencies(self, project_id: int) -> list[int]:
        result = await self._session.execute(
            select(ProjectDependencyModel.depends_on_id)
            .where(ProjectDependencyModel.project_id == project_id)
            .order_by(ProjectDependencyModel.depends_on_id)
        )
        return list(result.scalars().all())

    async def set_dependencies(self, project_id: int, depends_on: list[int]) -> None:
        await self._session.execute(
            delete(ProjectDependencyModel).where(
                ProjectDependencyModel.project_id == project_id
            )
        )
        for other_id in dict.fromkeys(depends_on):
            await self._session.execute(
                insert(ProjectDependencyModel).values(
                    project_id=project_id, depends_on_id=other_id
                )
            )
