"""Persistence of the replies written under a mission's updates."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.projects.domain.entities.update_comment import UpdateComment
from src.modules.projects.domain.repositories.update_comment_repository import (
    UpdateCommentRepository,
)
from src.modules.projects.infrastructure.database.models.project_update_model import (
    ProjectUpdateModel,
)
from src.modules.projects.infrastructure.database.models.update_comment_model import (
    UpdateCommentModel,
)


def _to_entity(model: UpdateCommentModel) -> UpdateComment:
    return UpdateComment(
        id=model.id,
        update_id=model.update_id,
        author_id=model.author_id,
        body=model.body,
        published_at=model.published_at,
        edited_at=model.edited_at,
        deleted_at=model.deleted_at,
    )


class SqlUpdateCommentRepository(UpdateCommentRepository):
    """The replies, in the database."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, comment_id: int) -> UpdateComment | None:
        model = await self._session.get(UpdateCommentModel, comment_id)
        return None if model is None else _to_entity(model)

    async def list_for_updates(
        self, update_ids: Sequence[int]
    ) -> dict[int, list[UpdateComment]]:
        if not update_ids:
            # A thread with no message asks nothing of the database.
            return {}

        result = await self._session.execute(
            select(UpdateCommentModel)
            .where(UpdateCommentModel.update_id.in_(update_ids))
            .order_by(UpdateCommentModel.published_at, UpdateCommentModel.id)
        )
        by_update: dict[int, list[UpdateComment]] = {}
        for model in result.scalars().all():
            by_update.setdefault(model.update_id, []).append(_to_entity(model))
        return by_update

    async def list_for_project(self, project_id: int) -> list[UpdateComment]:
        # The mission is carried by the update, not by the reply: a comment
        # knows the message it answers and nothing above it.
        result = await self._session.execute(
            select(UpdateCommentModel)
            .join(
                ProjectUpdateModel,
                ProjectUpdateModel.id == UpdateCommentModel.update_id,
            )
            .where(ProjectUpdateModel.project_id == project_id)
            .order_by(UpdateCommentModel.published_at, UpdateCommentModel.id)
        )
        return [_to_entity(model) for model in result.scalars().all()]

    async def authors_for_update(self, update_id: int) -> list[int]:
        result = await self._session.execute(
            select(UpdateCommentModel.author_id)
            .where(UpdateCommentModel.update_id == update_id)
            .order_by(UpdateCommentModel.published_at, UpdateCommentModel.id)
        )
        seen: list[int] = []
        for author_id in result.scalars().all():
            if author_id not in seen:
                seen.append(author_id)
        return seen

    async def add(self, comment: UpdateComment) -> UpdateComment:
        model = UpdateCommentModel(
            update_id=comment.update_id,
            author_id=comment.author_id,
            body=comment.body,
            published_at=comment.published_at,
        )
        self._session.add(model)
        await self._session.flush()
        comment.id = model.id
        return comment

    async def update(self, comment: UpdateComment) -> UpdateComment:
        assert comment.id is not None
        model = await self._session.get(UpdateCommentModel, comment.id)
        assert model is not None
        model.body = comment.body
        model.edited_at = comment.edited_at
        model.deleted_at = comment.deleted_at
        await self._session.flush()
        return comment
