"""SQLAlchemy implementation of the ProjectRepository port."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.projects.domain.entities.project import Project
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.infrastructure.database.models.project_model import (
    ProjectModel,
)


def to_entity(model: ProjectModel) -> Project:
    return Project(
        id=model.id,
        label=model.label,
        kind=model.kind,
        status=model.status,
        parent_id=model.parent_id,
        is_active=model.is_active,
        archived_at=model.archived_at,
        estimated_days=model.estimated_days,
        category=model.category,
        priority=model.priority,
        go_live_date=model.go_live_date,
        position=model.position,
        monday_item_id=model.monday_item_id,
        monday_subitem_id=model.monday_subitem_id,
        business_contacts=model.business_contacts,
        description=model.description,
    )


class SqlProjectRepository(ProjectRepository):
    """Persists the mission reference list."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, project_id: int) -> Project | None:
        model = await self._session.get(ProjectModel, project_id)
        return to_entity(model) if model else None

    async def list_all(self, include_inactive: bool = False) -> list[Project]:
        statement = select(ProjectModel).order_by(ProjectModel.label)
        if not include_inactive:
            statement = statement.where(ProjectModel.is_active.is_(True))
        result = await self._session.execute(statement)
        return [to_entity(model) for model in result.scalars().all()]

    async def list_children(self, parent_id: int) -> list[Project]:
        result = await self._session.execute(
            select(ProjectModel)
            .where(ProjectModel.parent_id == parent_id)
            .order_by(ProjectModel.label)
        )
        return [to_entity(model) for model in result.scalars().all()]

    async def add(self, project: Project) -> Project:
        model = ProjectModel(
            label=project.label,
            kind=project.kind,
            status=project.status,
            parent_id=project.parent_id,
            is_active=project.is_active,
            archived_at=project.archived_at,
            estimated_days=project.estimated_days,
            category=project.category,
            priority=project.priority,
            go_live_date=project.go_live_date,
            position=project.position,
            monday_item_id=project.monday_item_id,
            monday_subitem_id=project.monday_subitem_id,
            business_contacts=project.business_contacts,
            description=project.description,
        )
        self._session.add(model)
        await self._session.flush()
        project.id = model.id
        return project

    async def update(self, project: Project) -> Project:
        if project.id is None:
            return await self.add(project)
        model = await self._session.get(ProjectModel, project.id)
        if model is None:
            return project
        model.label = project.label
        model.kind = project.kind
        model.status = project.status
        model.parent_id = project.parent_id
        model.is_active = project.is_active
        model.archived_at = project.archived_at
        model.estimated_days = project.estimated_days
        model.category = project.category
        model.priority = project.priority
        model.go_live_date = project.go_live_date
        model.position = project.position
        model.monday_item_id = project.monday_item_id
        model.monday_subitem_id = project.monday_subitem_id
        model.business_contacts = project.business_contacts
        model.description = project.description
        await self._session.flush()
        return project

    async def delete(self, project_id: int) -> None:
        model = await self._session.get(ProjectModel, project_id)
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()
