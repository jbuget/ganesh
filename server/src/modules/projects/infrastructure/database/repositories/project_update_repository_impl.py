"""Persistance du fil de suivi d'une mission."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.projects.domain.repositories.project_update_repository import (
    ProjectUpdateRepository,
)
from src.modules.projects.infrastructure.database.models.project_update_model import (
    ProjectUpdateModel,
)


def _to_entity(model: ProjectUpdateModel) -> ProjectUpdate:
    return ProjectUpdate(
        id=model.id,
        project_id=model.project_id,
        author_id=model.author_id,
        texte=model.texte,
        publiee_le=model.publiee_le,
        modifiee_le=model.modifiee_le,
        supprimee_le=model.supprimee_le,
    )


class SqlProjectUpdateRepository(ProjectUpdateRepository):
    """Le fil, en base."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, update_id: int) -> ProjectUpdate | None:
        model = await self._session.get(ProjectUpdateModel, update_id)
        return None if model is None else _to_entity(model)

    async def list_for_project(self, project_id: int) -> list[ProjectUpdate]:
        result = await self._session.execute(
            select(ProjectUpdateModel)
            .where(ProjectUpdateModel.project_id == project_id)
            .order_by(
                ProjectUpdateModel.publiee_le.desc(), ProjectUpdateModel.id.desc()
            )
        )
        return [_to_entity(model) for model in result.scalars().all()]

    async def count_by_project(self) -> dict[int, int]:
        result = await self._session.execute(
            select(
                ProjectUpdateModel.project_id,
                func.count(ProjectUpdateModel.id),
            )
            .where(ProjectUpdateModel.supprimee_le.is_(None))
            .group_by(ProjectUpdateModel.project_id)
        )
        return dict(result.tuples().all())

    async def add(self, update: ProjectUpdate) -> ProjectUpdate:
        model = ProjectUpdateModel(
            project_id=update.project_id,
            author_id=update.author_id,
            texte=update.texte,
            publiee_le=update.publiee_le,
        )
        self._session.add(model)
        await self._session.flush()
        update.id = model.id
        return update

    async def update(self, update: ProjectUpdate) -> ProjectUpdate:
        assert update.id is not None
        model = await self._session.get(ProjectUpdateModel, update.id)
        assert model is not None
        model.texte = update.texte
        model.modifiee_le = update.modifiee_le
        model.supprimee_le = update.supprimee_le
        await self._session.flush()
        return update
