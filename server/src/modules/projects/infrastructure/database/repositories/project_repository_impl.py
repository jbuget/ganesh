"""Implementation SQLAlchemy du port ProjectRepository."""

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
        statut=model.statut,
        parent_id=model.parent_id,
        actif=model.actif,
        estime_j=model.estime_j,
        monday_item_id=model.monday_item_id,
        monday_subitem_id=model.monday_subitem_id,
    )


class SqlProjectRepository(ProjectRepository):
    """Persiste le referentiel des missions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, project_id: int) -> Project | None:
        model = await self._session.get(ProjectModel, project_id)
        return to_entity(model) if model else None

    async def list_all(self, include_inactive: bool = False) -> list[Project]:
        statement = select(ProjectModel).order_by(ProjectModel.label)
        if not include_inactive:
            statement = statement.where(ProjectModel.actif.is_(True))
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
            statut=project.statut,
            parent_id=project.parent_id,
            actif=project.actif,
            estime_j=project.estime_j,
            monday_item_id=project.monday_item_id,
            monday_subitem_id=project.monday_subitem_id,
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
        model.statut = project.statut
        model.parent_id = project.parent_id
        model.actif = project.actif
        model.estime_j = project.estime_j
        model.monday_item_id = project.monday_item_id
        model.monday_subitem_id = project.monday_subitem_id
        await self._session.flush()
        return project
