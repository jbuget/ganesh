"""SQLAlchemy implementation of the MoodRepository port."""

from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.moods.domain.entities.mood import Mood
from src.modules.moods.domain.repositories.mood_repository import MoodRepository
from src.modules.moods.infrastructure.database.models.mood_model import MoodModel


def to_entity(model: MoodModel) -> Mood:
    return Mood(id=model.id, user_id=model.user_id, day=model.day, level=model.level)


class SqlMoodRepository(MoodRepository):
    """Persists the moods the team posts."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _get_model(self, user_id: int, day: date) -> MoodModel | None:
        result = await self._session.execute(
            select(MoodModel).where(
                and_(MoodModel.user_id == user_id, MoodModel.day == day)
            )
        )
        return result.scalar_one_or_none()

    async def get(self, user_id: int, day: date) -> Mood | None:
        model = await self._get_model(user_id, day)
        return to_entity(model) if model else None

    async def list_between(self, start: date, end: date) -> list[Mood]:
        result = await self._session.execute(
            select(MoodModel)
            .where(and_(MoodModel.day >= start, MoodModel.day <= end))
            .order_by(MoodModel.day, MoodModel.user_id)
        )
        return [to_entity(model) for model in result.scalars().all()]

    async def list_for_user_between(
        self, user_id: int, start: date, end: date
    ) -> list[Mood]:
        result = await self._session.execute(
            select(MoodModel)
            .where(
                and_(
                    MoodModel.user_id == user_id,
                    MoodModel.day >= start,
                    MoodModel.day <= end,
                )
            )
            .order_by(MoodModel.day)
        )
        return [to_entity(model) for model in result.scalars().all()]

    async def upsert(self, mood: Mood) -> Mood:
        model = await self._get_model(mood.user_id, mood.day)
        if model is None:
            model = MoodModel(user_id=mood.user_id, day=mood.day, level=mood.level)
            self._session.add(model)
        else:
            model.level = mood.level
        await self._session.flush()
        mood.id = model.id
        return mood
