"""SQLAlchemy implementation of the UserMissionRepository port."""

from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.entries.domain.repositories.user_mission_repository import (
    UserMissionRepository,
)
from src.modules.entries.infrastructure.database.models.entry_model import (
    UserMissionModel,
)
from src.modules.months.domain.services.month_period import first_day_of


class SqlUserMissionRepository(UserMissionRepository):
    """Persists the missions a user put on a month.

    A month is held by its first day, whatever day the caller hands over: the
    unique key says one mission once per month, and a row dated the 24th would
    slip past it.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _get_model(
        self, user_id: int, project_id: int, month: date
    ) -> UserMissionModel | None:
        result = await self._session.execute(
            select(UserMissionModel).where(
                and_(
                    UserMissionModel.user_id == user_id,
                    UserMissionModel.project_id == project_id,
                    UserMissionModel.month == first_day_of(month),
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_for_month(self, user_id: int, month: date) -> list[int]:
        result = await self._session.execute(
            select(UserMissionModel.project_id)
            .where(
                and_(
                    UserMissionModel.user_id == user_id,
                    UserMissionModel.month == first_day_of(month),
                )
            )
            .order_by(UserMissionModel.project_id)
        )
        return list(result.scalars().all())

    async def add(self, user_id: int, project_id: int, month: date) -> None:
        if await self._get_model(user_id, project_id, month) is not None:
            return
        self._session.add(
            UserMissionModel(
                user_id=user_id,
                project_id=project_id,
                month=first_day_of(month),
            )
        )
        await self._session.flush()

    async def remove(self, user_id: int, project_id: int, month: date) -> None:
        model = await self._get_model(user_id, project_id, month)
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()
