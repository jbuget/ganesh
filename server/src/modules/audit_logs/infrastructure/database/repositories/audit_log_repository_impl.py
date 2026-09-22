"""SQLAlchemy implementation of the AuditLogRepository port."""

from collections.abc import Collection
from datetime import date, datetime

from sqlalchemy import and_, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql.elements import ColumnElement

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.audit_logs.infrastructure.database.models.audit_log_model import (
    AuditLogModel,
)


def to_entity(model: AuditLogModel) -> AuditLog:
    return AuditLog(
        id=model.id,
        action=model.action,
        actor_id=model.actor_id or 0,
        at=model.at,
        target_user_id=model.target_user_id,
        project_id=model.project_id,
        request_id=model.request_id,
        day=model.day,
        old_value=model.old_value,
        new_value=model.new_value,
        payload=model.payload,
    )


class SqlAuditLogRepository(AuditLogRepository):
    """Persists the audit log."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, log: AuditLog) -> AuditLog:
        model = AuditLogModel(
            action=log.action,
            actor_id=log.actor_id,
            at=log.at,
            target_user_id=log.target_user_id,
            project_id=log.project_id,
            request_id=log.request_id,
            day=log.day,
            old_value=log.old_value,
            new_value=log.new_value,
            payload=log.payload,
        )
        self._session.add(model)
        await self._session.flush()
        log.id = model.id
        return log

    @staticmethod
    def _within_the_month(target_user_id: int, month: date) -> ColumnElement[bool]:
        return and_(
            AuditLogModel.target_user_id == target_user_id,
            extract("year", AuditLogModel.day) == month.year,
            extract("month", AuditLogModel.day) == month.month,
        )

    async def list_for_user_month(
        self, target_user_id: int, month: date, limit: int, offset: int
    ) -> list[AuditLog]:
        result = await self._session.execute(
            select(AuditLogModel)
            .where(self._within_the_month(target_user_id, month))
            # The id breaks the tie, as it does on a mission's log: a page that
            # reordered lines sharing a timestamp would show one of them twice.
            .order_by(AuditLogModel.at.desc(), AuditLogModel.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return [to_entity(model) for model in result.scalars().all()]

    async def count_for_user_month(self, target_user_id: int, month: date) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(AuditLogModel)
            .where(self._within_the_month(target_user_id, month))
        )
        return int(result.scalar_one())

    async def list_for_project(
        self, project_id: int, limit: int, offset: int
    ) -> list[AuditLog]:
        # The id breaks the tie: several lines share a timestamp whenever one
        # gesture changed several fields, and a page that reordered them
        # between two reads would show the same line twice.
        result = await self._session.execute(
            select(AuditLogModel)
            .where(AuditLogModel.project_id == project_id)
            .order_by(AuditLogModel.at.desc(), AuditLogModel.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return [to_entity(model) for model in result.scalars().all()]

    async def count_for_project(self, project_id: int) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(AuditLogModel)
            .where(AuditLogModel.project_id == project_id)
        )
        return result.scalar_one()

    async def list_all(
        self, limit: int, offset: int, since: datetime | None = None
    ) -> list[AuditLog]:
        query = select(AuditLogModel)
        if since is not None:
            query = query.where(AuditLogModel.at >= since)
        # The same tie-break as a mission's page, for the same reason: one
        # gesture that changed several fields wrote several lines at one
        # timestamp, and a page reordering them would show one twice.
        result = await self._session.execute(
            query.order_by(AuditLogModel.at.desc(), AuditLogModel.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return [to_entity(model) for model in result.scalars().all()]

    async def count_all(self, since: datetime | None = None) -> int:
        query = select(func.count()).select_from(AuditLogModel)
        if since is not None:
            query = query.where(AuditLogModel.at >= since)
        result = await self._session.execute(query)
        return result.scalar_one()

    async def list_between(
        self,
        start: datetime,
        end: datetime,
        actions: Collection[AuditAction] | None = None,
    ) -> list[AuditLog]:
        query = select(AuditLogModel).where(
            and_(AuditLogModel.at >= start, AuditLogModel.at <= end)
        )
        if actions is not None:
            query = query.where(AuditLogModel.action.in_(list(actions)))
        result = await self._session.execute(
            query.order_by(AuditLogModel.at, AuditLogModel.id)
        )
        return [to_entity(model) for model in result.scalars().all()]

    async def last_touch_per_project(
        self, actions: Collection[AuditAction], limit: int
    ) -> list[AuditLog]:
        # `DISTINCT ON` keeps the first row of each project once ordered, which
        # is Postgres saying « the latest line of each » in one pass. The
        # ordering it demands is by project; the freshest-first order the
        # caller reads is put back on the outside.
        latest = (
            select(AuditLogModel)
            .where(AuditLogModel.project_id.is_not(None))
            .where(AuditLogModel.action.in_(list(actions)))
            .distinct(AuditLogModel.project_id)
            .order_by(
                AuditLogModel.project_id,
                AuditLogModel.at.desc(),
                AuditLogModel.id.desc(),
            )
            .subquery()
        )
        newest = aliased(AuditLogModel, latest)
        result = await self._session.execute(
            select(newest).order_by(newest.at.desc(), newest.id.desc()).limit(limit)
        )
        return [to_entity(model) for model in result.scalars().all()]
