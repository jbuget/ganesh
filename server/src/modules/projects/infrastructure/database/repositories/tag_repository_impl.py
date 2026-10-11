"""Persistence of the vocabulary of tags."""

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.projects.domain.entities.tag import Tag, TagUsage
from src.modules.projects.domain.repositories.tag_repository import TagRepository
from src.modules.projects.infrastructure.database.models.tag_link_model import (
    TagLinkModel,
)
from src.modules.projects.infrastructure.database.models.tag_model import TagModel


def _to_entity(model: TagModel) -> Tag:
    return Tag(id=model.id, name=model.name, color=model.color)


class SqlTagRepository(TagRepository):
    """Tags stored in their own table."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, tag: Tag) -> Tag:
        model = TagModel(name=tag.name, key=tag.key, color=tag.color)
        self._session.add(model)
        await self._session.flush()
        return _to_entity(model)

    async def get_by_id(self, tag_id: int) -> Tag | None:
        model = await self._session.get(TagModel, tag_id)
        return _to_entity(model) if model else None

    async def get_by_key(self, key: str) -> Tag | None:
        result = await self._session.execute(
            select(TagModel).where(TagModel.key == key)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def update(self, tag: Tag) -> Tag:
        model = await self._session.get(TagModel, tag.id)
        if model is None:
            raise ValueError(f"No tag with id {tag.id}.")

        model.name = tag.name
        model.key = tag.key
        model.color = tag.color
        await self._session.flush()
        return _to_entity(model)

    async def delete(self, tag_id: int) -> None:
        await self._session.execute(delete(TagModel).where(TagModel.id == tag_id))

    async def list_in_use(self) -> list[TagUsage]:
        count = func.count(TagLinkModel.project_id)
        result = await self._session.execute(
            select(TagModel, count)
            .join(TagLinkModel, TagLinkModel.tag_id == TagModel.id)
            .group_by(TagModel.id)
            .order_by(count.desc(), TagModel.key)
        )
        return [TagUsage(_to_entity(model), total) for model, total in result.all()]
