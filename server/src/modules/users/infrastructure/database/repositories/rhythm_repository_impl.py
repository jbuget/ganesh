"""SQLAlchemy implementation of the RhythmRepository port."""

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import replace

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.calendar.domain.entities.week_pattern import WeekPattern
from src.modules.users.domain.entities.rhythm import Rhythm, RhythmHistory
from src.modules.users.domain.repositories.rhythm_repository import RhythmRepository
from src.modules.users.infrastructure.database.models.rhythm_model import (
    WorkRhythmModel,
)


def to_entity(model: WorkRhythmModel) -> Rhythm:
    return Rhythm(
        id=model.id,
        user_id=model.user_id,
        pattern=WeekPattern(
            monday=model.monday,
            tuesday=model.tuesday,
            wednesday=model.wednesday,
            thursday=model.thursday,
            friday=model.friday,
        ),
        effective_from=model.effective_from,
    )


class SqlRhythmRepository(RhythmRepository):
    """Persists declared rhythms in the database."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def history_of(self, user_id: int) -> RhythmHistory:
        result = await self._session.execute(
            select(WorkRhythmModel).where(WorkRhythmModel.user_id == user_id)
        )
        return RhythmHistory.of(to_entity(model) for model in result.scalars().all())

    async def histories_of(self, user_ids: Sequence[int]) -> dict[int, RhythmHistory]:
        if not user_ids:
            return {}

        result = await self._session.execute(
            select(WorkRhythmModel).where(WorkRhythmModel.user_id.in_(user_ids))
        )

        declared: dict[int, list[Rhythm]] = defaultdict(list)
        for model in result.scalars().all():
            declared[model.user_id].append(to_entity(model))

        # Everyone asked for comes back, those who declared nothing included:
        # an empty history is an answer — full time — and a caller that had to
        # tell a missing key from an empty one would rebuild that default.
        return {
            user_id: RhythmHistory.of(declared.get(user_id, ())) for user_id in user_ids
        }

    async def declare(self, rhythm: Rhythm) -> Rhythm:
        result = await self._session.execute(
            select(WorkRhythmModel).where(
                WorkRhythmModel.user_id == rhythm.user_id,
                WorkRhythmModel.effective_from == rhythm.effective_from,
            )
        )
        model = result.scalar_one_or_none()

        if model is None:
            model = WorkRhythmModel(
                user_id=rhythm.user_id, effective_from=rhythm.effective_from
            )
            self._session.add(model)

        model.monday = rhythm.pattern.monday
        model.tuesday = rhythm.pattern.tuesday
        model.wednesday = rhythm.pattern.wednesday
        model.thursday = rhythm.pattern.thursday
        model.friday = rhythm.pattern.friday

        await self._session.flush()
        return replace(rhythm, id=model.id)
