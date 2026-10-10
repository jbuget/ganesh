"""Persistence of a mission's follow-up thread."""

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
        body=model.body,
        published_at=model.published_at,
        edited_at=model.edited_at,
        deleted_at=model.deleted_at,
    )


class SqlProjectUpdateRepository(ProjectUpdateRepository):
    """The thread, in the database."""

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
                ProjectUpdateModel.published_at.desc(), ProjectUpdateModel.id.desc()
            )
        )
        return [_to_entity(model) for model in result.scalars().all()]

    async def count_by_project(self) -> dict[int, int]:
        result = await self._session.execute(
            select(
                ProjectUpdateModel.project_id,
                func.count(ProjectUpdateModel.id),
            )
            .where(ProjectUpdateModel.deleted_at.is_(None))
            .group_by(ProjectUpdateModel.project_id)
        )
        return dict(result.tuples().all())

    async def latest_by_project(self) -> dict[int, ProjectUpdate]:
        # Withdrawn ones are ruled out before sorting, not after: the latest
        # readable update of a thread is not always the last one written.
        live = (
            select(ProjectUpdateModel)
            .where(ProjectUpdateModel.deleted_at.is_(None))
            .order_by(
                ProjectUpdateModel.project_id,
                ProjectUpdateModel.published_at.desc(),
                ProjectUpdateModel.id.desc(),
            )
            .distinct(ProjectUpdateModel.project_id)
        )
        result = await self._session.execute(live)
        return {model.project_id: _to_entity(model) for model in result.scalars().all()}

    async def authors_for_project(self, project_id: int) -> set[int]:
        result = await self._session.execute(
            select(ProjectUpdateModel.author_id).where(
                ProjectUpdateModel.project_id == project_id
            )
        )
        return set(result.scalars().all())

    async def add(self, update: ProjectUpdate) -> ProjectUpdate:
        model = ProjectUpdateModel(
            project_id=update.project_id,
            author_id=update.author_id,
            body=update.body,
            published_at=update.published_at,
        )
        self._session.add(model)
        await self._session.flush()
        update.id = model.id
        return update

    async def update(self, update: ProjectUpdate) -> ProjectUpdate:
        assert update.id is not None
        model = await self._session.get(ProjectUpdateModel, update.id)
        assert model is not None
        model.body = update.body
        model.edited_at = update.edited_at
        model.deleted_at = update.deleted_at
        await self._session.flush()
        return update
