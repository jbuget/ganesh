"""Persistence of the tags a mission carries."""

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.projects.domain.entities.tag import Tag
from src.modules.projects.domain.repositories.project_tag_repository import (
    ProjectTagRepository,
)
from src.modules.projects.infrastructure.database.models.tag_link_model import (
    TagLinkModel,
)
from src.modules.projects.infrastructure.database.models.tag_model import TagModel


class SqlProjectTagRepository(ProjectTagRepository):
    """Tags carried, stored in the join table."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_project(self, project_id: int) -> list[Tag]:
        result = await self._session.execute(
            select(TagModel)
            .join(TagLinkModel, TagLinkModel.tag_id == TagModel.id)
            .where(TagLinkModel.project_id == project_id)
            .order_by(TagModel.key)
        )
        return [
            Tag(id=m.id, name=m.name, color=m.color) for m in result.scalars().all()
        ]

    async def list_all(self) -> dict[int, list[Tag]]:
        """Every mark at once: the reference list and the board read them by the
        dozen."""
        result = await self._session.execute(
            select(TagLinkModel.project_id, TagModel)
            .join(TagModel, TagModel.id == TagLinkModel.tag_id)
            .order_by(TagModel.key)
        )
        by_project: dict[int, list[Tag]] = {}
        for project_id, model in result.all():
            by_project.setdefault(project_id, []).append(
                Tag(id=model.id, name=model.name, color=model.color)
            )
        return by_project

    async def project_ids_for(self, tag_id: int) -> list[int]:
        result = await self._session.execute(
            select(TagLinkModel.project_id)
            .where(TagLinkModel.tag_id == tag_id)
            .order_by(TagLinkModel.project_id)
        )
        return list(result.scalars().all())

    async def attach(self, project_id: int, tag_id: int) -> None:
        # The primary key carries both columns: letting the database ignore the
        # duplicate saves a round trip to check on every click.
        await self._session.execute(
            insert(TagLinkModel)
            .values(project_id=project_id, tag_id=tag_id)
            .on_conflict_do_nothing()
        )

    async def detach(self, project_id: int, tag_id: int) -> None:
        await self._session.execute(
            delete(TagLinkModel).where(
                TagLinkModel.project_id == project_id,
                TagLinkModel.tag_id == tag_id,
            )
        )
