"""SQLAlchemy implementation of the EntryRepository port."""

from datetime import date

from sqlalchemy import and_, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.entries.infrastructure.database.models.entry_model import EntryModel
from src.modules.projects.domain.entities.project import ProjectStatus


def to_entity(model: EntryModel) -> Entry:
    return Entry(
        id=model.id,
        user_id=model.user_id,
        project_id=model.project_id,
        day=model.day,
        value=DayValue(model.value),
        status_at_entry=model.status_at_entry,
    )


class SqlEntryRepository(EntryRepository):
    """Persists time entries."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _get_model(
        self, user_id: int, project_id: int, day: date
    ) -> EntryModel | None:
        result = await self._session.execute(
            select(EntryModel).where(
                and_(
                    EntryModel.user_id == user_id,
                    EntryModel.project_id == project_id,
                    EntryModel.day == day,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get(self, user_id: int, project_id: int, day: date) -> Entry | None:
        model = await self._get_model(user_id, project_id, day)
        return to_entity(model) if model else None

    async def list_for_month(self, user_id: int, month: date) -> list[Entry]:
        result = await self._session.execute(
            select(EntryModel)
            .where(
                and_(
                    EntryModel.user_id == user_id,
                    extract("year", EntryModel.day) == month.year,
                    extract("month", EntryModel.day) == month.month,
                )
            )
            .order_by(EntryModel.day)
        )
        return [to_entity(model) for model in result.scalars().all()]

    async def list_for_user_between(
        self, user_id: int, start: date, end: date
    ) -> list[Entry]:
        result = await self._session.execute(
            select(EntryModel)
            .where(
                and_(
                    EntryModel.user_id == user_id,
                    EntryModel.day >= start,
                    EntryModel.day <= end,
                )
            )
            .order_by(EntryModel.day)
        )
        return [to_entity(model) for model in result.scalars().all()]

    async def list_for_day(self, user_id: int, day: date) -> list[Entry]:
        result = await self._session.execute(
            select(EntryModel).where(
                and_(EntryModel.user_id == user_id, EntryModel.day == day)
            )
        )
        return [to_entity(model) for model in result.scalars().all()]

    async def list_for_project(self, project_id: int) -> list[Entry]:
        result = await self._session.execute(
            select(EntryModel)
            .where(EntryModel.project_id == project_id)
            .order_by(EntryModel.day)
        )
        return [to_entity(model) for model in result.scalars().all()]

    async def count_by_project(self) -> dict[int, int]:
        result = await self._session.execute(
            select(EntryModel.project_id, func.count()).group_by(EntryModel.project_id)
        )
        return dict(result.all())  # type: ignore[arg-type]

    async def sum_realised_by_project(self, today: date) -> dict[int, float]:
        result = await self._session.execute(
            select(EntryModel.project_id, func.sum(EntryModel.value))
            .where(EntryModel.day <= today)
            .group_by(EntryModel.project_id)
        )
        return {project_id: float(total) for project_id, total in result.all()}

    async def sum_realised_by_project_and_status(
        self, today: date, since: date | None = None
    ) -> dict[int, dict[ProjectStatus | None, float]]:
        query = (
            select(
                EntryModel.project_id,
                EntryModel.status_at_entry,
                func.sum(EntryModel.value),
            )
            .where(EntryModel.day <= today)
            .group_by(EntryModel.project_id, EntryModel.status_at_entry)
        )
        if since is not None:
            query = query.where(EntryModel.day >= since)

        sums: dict[int, dict[ProjectStatus | None, float]] = {}
        for project_id, status, total in (await self._session.execute(query)).all():
            sums.setdefault(project_id, {})[status] = float(total)
        return sums

    async def span_by_project(self) -> dict[int, tuple[date, date]]:
        result = await self._session.execute(
            select(
                EntryModel.project_id,
                func.min(EntryModel.day),
                func.max(EntryModel.day),
            ).group_by(EntryModel.project_id)
        )
        return {project_id: (first, last) for project_id, first, last in result.all()}

    async def sum_forecast_by_project(self, today: date) -> dict[int, float]:
        result = await self._session.execute(
            select(EntryModel.project_id, func.sum(EntryModel.value))
            .where(EntryModel.day > today)
            .group_by(EntryModel.project_id)
        )
        return {project_id: float(total) for project_id, total in result.all()}

    async def sum_by_user_and_day(
        self, start: date, end: date
    ) -> dict[int, dict[date, float]]:
        result = await self._session.execute(
            select(EntryModel.user_id, EntryModel.day, func.sum(EntryModel.value))
            .where(and_(EntryModel.day >= start, EntryModel.day <= end))
            .group_by(EntryModel.user_id, EntryModel.day)
        )
        diaries: dict[int, dict[date, float]] = {}
        for user_id, day, total in result.all():
            diaries.setdefault(user_id, {})[day] = float(total)
        return diaries

    async def list_over(self, start: date, end: date) -> list[Entry]:
        result = await self._session.execute(
            select(EntryModel)
            .where(and_(EntryModel.day >= start, EntryModel.day <= end))
            .order_by(EntryModel.day, EntryModel.user_id, EntryModel.project_id)
        )
        return [to_entity(model) for model in result.scalars().all()]

    async def upsert(self, entry: Entry) -> Entry:
        model = await self._get_model(entry.user_id, entry.project_id, entry.day)
        if model is None:
            model = EntryModel(
                user_id=entry.user_id,
                project_id=entry.project_id,
                day=entry.day,
                value=float(entry.value),
                status_at_entry=entry.status_at_entry,
            )
            self._session.add(model)
        else:
            model.value = float(entry.value)
            model.status_at_entry = entry.status_at_entry
        await self._session.flush()
        entry.id = model.id
        return entry

    async def delete(self, user_id: int, project_id: int, day: date) -> None:
        model = await self._get_model(user_id, project_id, day)
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()
