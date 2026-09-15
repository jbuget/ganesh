"""Implementation SQLAlchemy du port EntryRepository."""

from datetime import date

from sqlalchemy import and_, extract, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.entries.infrastructure.database.models.entry_model import EntryModel


def to_entity(model: EntryModel) -> Entry:
    return Entry(
        id=model.id,
        user_id=model.user_id,
        project_id=model.project_id,
        jour=model.jour,
        valeur=DayValue(model.valeur),
        statut_at_entry=model.statut_at_entry,
    )


class SqlEntryRepository(EntryRepository):
    """Persiste les saisies de temps."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _get_model(
        self, user_id: int, project_id: int, jour: date
    ) -> EntryModel | None:
        result = await self._session.execute(
            select(EntryModel).where(
                and_(
                    EntryModel.user_id == user_id,
                    EntryModel.project_id == project_id,
                    EntryModel.jour == jour,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get(self, user_id: int, project_id: int, jour: date) -> Entry | None:
        model = await self._get_model(user_id, project_id, jour)
        return to_entity(model) if model else None

    async def list_for_month(self, user_id: int, mois: date) -> list[Entry]:
        result = await self._session.execute(
            select(EntryModel)
            .where(
                and_(
                    EntryModel.user_id == user_id,
                    extract("year", EntryModel.jour) == mois.year,
                    extract("month", EntryModel.jour) == mois.month,
                )
            )
            .order_by(EntryModel.jour)
        )
        return [to_entity(model) for model in result.scalars().all()]

    async def list_for_day(self, user_id: int, jour: date) -> list[Entry]:
        result = await self._session.execute(
            select(EntryModel).where(
                and_(EntryModel.user_id == user_id, EntryModel.jour == jour)
            )
        )
        return [to_entity(model) for model in result.scalars().all()]

    async def list_for_project(self, project_id: int) -> list[Entry]:
        result = await self._session.execute(
            select(EntryModel)
            .where(EntryModel.project_id == project_id)
            .order_by(EntryModel.jour)
        )
        return [to_entity(model) for model in result.scalars().all()]

    async def upsert(self, entry: Entry) -> Entry:
        model = await self._get_model(entry.user_id, entry.project_id, entry.jour)
        if model is None:
            model = EntryModel(
                user_id=entry.user_id,
                project_id=entry.project_id,
                jour=entry.jour,
                valeur=float(entry.valeur),
                statut_at_entry=entry.statut_at_entry,
            )
            self._session.add(model)
        else:
            model.valeur = float(entry.valeur)
            model.statut_at_entry = entry.statut_at_entry
        await self._session.flush()
        entry.id = model.id
        return entry

    async def delete(self, user_id: int, project_id: int, jour: date) -> None:
        model = await self._get_model(user_id, project_id, jour)
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()
