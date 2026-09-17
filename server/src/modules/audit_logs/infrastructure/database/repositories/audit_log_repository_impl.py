"""Implementation SQLAlchemy du port AuditLogRepository."""

from datetime import date

from sqlalchemy import and_, extract, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.audit_logs.domain.entities.audit_log import AuditLog
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
        jour=model.jour,
        old_value=model.old_value,
        new_value=model.new_value,
        payload=model.payload,
    )


class SqlAuditLogRepository(AuditLogRepository):
    """Persiste le journal d'audit."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, log: AuditLog) -> AuditLog:
        model = AuditLogModel(
            action=log.action,
            actor_id=log.actor_id,
            at=log.at,
            target_user_id=log.target_user_id,
            project_id=log.project_id,
            jour=log.jour,
            old_value=log.old_value,
            new_value=log.new_value,
            payload=log.payload,
        )
        self._session.add(model)
        await self._session.flush()
        log.id = model.id
        return log

    async def list_for_user_month(
        self, target_user_id: int, mois: date
    ) -> list[AuditLog]:
        result = await self._session.execute(
            select(AuditLogModel)
            .where(
                and_(
                    AuditLogModel.target_user_id == target_user_id,
                    extract("year", AuditLogModel.jour) == mois.year,
                    extract("month", AuditLogModel.jour) == mois.month,
                )
            )
            .order_by(AuditLogModel.at.desc())
        )
        return [to_entity(model) for model in result.scalars().all()]

    async def list_for_project(self, project_id: int) -> list[AuditLog]:
        result = await self._session.execute(
            select(AuditLogModel)
            .where(AuditLogModel.project_id == project_id)
            .order_by(AuditLogModel.at.desc())
        )
        return [to_entity(model) for model in result.scalars().all()]
