"""Implementation SQLAlchemy du port MonthRepository."""

from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.months.domain.entities.month import Month
from src.modules.months.domain.repositories.month_repository import MonthRepository
from src.modules.months.infrastructure.database.models.month_model import MonthModel


def to_entity(model: MonthModel) -> Month:
    return Month(
        id=model.id,
        user_id=model.user_id,
        month=model.month,
        state=model.state,
        validated_at=model.validated_at,
        validated_by=model.validated_by,
        reopened_at=model.reopened_at,
        reopened_by=model.reopened_by,
    )


class SqlMonthRepository(MonthRepository):
    """Persiste l'etat de saisie des mois."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: int, month: date) -> Month | None:
        result = await self._session.execute(
            select(MonthModel).where(
                and_(
                    MonthModel.user_id == user_id,
                    MonthModel.month == month.replace(day=1),
                )
            )
        )
        model = result.scalar_one_or_none()
        return to_entity(model) if model else None

    async def list_for_month(self, month: date) -> list[Month]:
        result = await self._session.execute(
            select(MonthModel).where(MonthModel.month == month.replace(day=1))
        )
        return [to_entity(model) for model in result.scalars().all()]

    async def save(self, month: Month) -> Month:
        result = await self._session.execute(
            select(MonthModel).where(
                and_(
                    MonthModel.user_id == month.user_id, MonthModel.month == month.month
                )
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            model = MonthModel(user_id=month.user_id, month=month.month)
            self._session.add(model)
        model.state = month.state
        model.validated_at = month.validated_at
        model.validated_by = month.validated_by
        model.reopened_at = month.reopened_at
        model.reopened_by = month.reopened_by
        await self._session.flush()
        month.id = model.id
        return month
