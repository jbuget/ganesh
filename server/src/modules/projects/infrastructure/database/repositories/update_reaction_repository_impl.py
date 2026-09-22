"""Persistence of the signs left under an update."""

from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.projects.domain.entities.update_reaction import (
    Reaction,
    UpdateReaction,
)
from src.modules.projects.domain.repositories.update_reaction_repository import (
    UpdateReactionRepository,
)
from src.modules.projects.infrastructure.database.models.update_reaction_model import (
    UpdateReactionModel,
)


class SqlUpdateReactionRepository(UpdateReactionRepository):
    """The reactions, in the database."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_updates(
        self, update_ids: Sequence[int]
    ) -> dict[int, list[UpdateReaction]]:
        if not update_ids:
            # A thread with no message asks nothing of the database.
            return {}

        result = await self._session.execute(
            select(UpdateReactionModel)
            .where(UpdateReactionModel.update_id.in_(update_ids))
            .order_by(UpdateReactionModel.at)
        )
        by_update: dict[int, list[UpdateReaction]] = {}
        for model in result.scalars().all():
            by_update.setdefault(model.update_id, []).append(
                UpdateReaction(
                    update_id=model.update_id,
                    user_id=model.user_id,
                    reaction=model.reaction,
                    at=model.at,
                )
            )
        return by_update

    async def add(self, reaction: UpdateReaction) -> None:
        # The key carries the three columns, so leaving the same sign again is
        # a no-op rather than a clash: the second click keeps the first date.
        await self._session.execute(
            insert(UpdateReactionModel)
            .values(
                update_id=reaction.update_id,
                user_id=reaction.user_id,
                reaction=reaction.reaction,
                at=reaction.at,
            )
            .on_conflict_do_nothing()
        )

    async def remove(self, update_id: int, user_id: int, reaction: Reaction) -> None:
        await self._session.execute(
            delete(UpdateReactionModel).where(
                UpdateReactionModel.update_id == update_id,
                UpdateReactionModel.user_id == user_id,
                UpdateReactionModel.reaction == reaction,
            )
        )
