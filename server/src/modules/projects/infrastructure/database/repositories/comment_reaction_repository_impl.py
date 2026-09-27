"""Persistence of the signs left under a reply."""

from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.projects.domain.entities.comment_reaction import CommentReaction
from src.modules.projects.domain.entities.update_reaction import Reaction
from src.modules.projects.domain.repositories.comment_reaction_repository import (
    CommentReactionRepository,
)
from src.modules.projects.infrastructure.database.models.comment_reaction_model import (
    CommentReactionModel,
)


class SqlCommentReactionRepository(CommentReactionRepository):
    """The signs left under the replies, in the database."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_comments(
        self, comment_ids: Sequence[int]
    ) -> dict[int, list[CommentReaction]]:
        if not comment_ids:
            # A conversation with no reply asks nothing of the database.
            return {}

        result = await self._session.execute(
            select(CommentReactionModel)
            .where(CommentReactionModel.comment_id.in_(comment_ids))
            .order_by(CommentReactionModel.at)
        )
        by_comment: dict[int, list[CommentReaction]] = {}
        for model in result.scalars().all():
            by_comment.setdefault(model.comment_id, []).append(
                CommentReaction(
                    comment_id=model.comment_id,
                    user_id=model.user_id,
                    reaction=model.reaction,
                    at=model.at,
                )
            )
        return by_comment

    async def add(self, reaction: CommentReaction) -> None:
        # The key carries the three columns, so leaving the same sign again is
        # a no-op rather than a clash: the second click keeps the first date.
        await self._session.execute(
            insert(CommentReactionModel)
            .values(
                comment_id=reaction.comment_id,
                user_id=reaction.user_id,
                reaction=reaction.reaction,
                at=reaction.at,
            )
            .on_conflict_do_nothing()
        )

    async def remove(self, comment_id: int, user_id: int, reaction: Reaction) -> None:
        await self._session.execute(
            delete(CommentReactionModel).where(
                CommentReactionModel.comment_id == comment_id,
                CommentReactionModel.user_id == user_id,
                CommentReactionModel.reaction == reaction,
            )
        )
