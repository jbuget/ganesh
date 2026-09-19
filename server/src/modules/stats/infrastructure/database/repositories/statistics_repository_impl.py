"""SQLAlchemy implementation of the StatisticsRepository port."""

from datetime import date

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.audit_logs.infrastructure.database.models.audit_log_model import (
    AuditLogModel,
)
from src.modules.entries.infrastructure.database.models.entry_model import EntryModel
from src.modules.months.domain.entities.month import MonthState
from src.modules.months.infrastructure.database.models.month_model import MonthModel
from src.modules.projects.domain.entities.project import (
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.infrastructure.database.models.project_model import (
    ProjectModel,
)
from src.modules.stats.domain.entities.period import Period
from src.modules.stats.domain.repositories.statistics_repository import (
    StatisticsRepository,
)


class SqlStatisticsRepository(StatisticsRepository):
    """Counts the window straight in the database.

    Every figure is an aggregate: the dashboard never walks a list of entries
    to work out a percentage, however small the team is today.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _within(self, period: Period) -> ColumnElement[bool]:
        return EntryModel.day.between(period.start, period.end)

    async def declared_days(self, period: Period) -> float:
        total = await self._session.scalar(
            select(func.coalesce(func.sum(EntryModel.value), 0.0)).where(
                self._within(period)
            )
        )
        return float(total or 0.0)

    async def contributor_ids(self, period: Period) -> set[int]:
        rows = await self._session.execute(
            select(EntryModel.user_id).where(self._within(period)).distinct()
        )
        return {user_id for (user_id,) in rows.all()}

    async def entry_delays(self, period: Period) -> list[int]:
        """How long each entry of the window waited before being written.

        Read from the audit log rather than from the entries: `updated_at`
        moves on every correction, while the log keeps the moment the day was
        first declared.
        """
        rows = await self._session.execute(
            select(AuditLogModel.at, AuditLogModel.day).where(
                and_(
                    AuditLogModel.action == AuditAction.ENTRY_SET,
                    AuditLogModel.day.is_not(None),
                    func.date(AuditLogModel.at).between(period.start, period.end),
                )
            )
        )
        return [max(0, (at.date() - day).days) for at, day in rows.all()]

    async def days_by_kind(self, period: Period) -> dict[ProjectKind, float]:
        rows = await self._session.execute(
            select(ProjectModel.kind, func.sum(EntryModel.value))
            .join(ProjectModel, ProjectModel.id == EntryModel.project_id)
            .where(self._within(period))
            .group_by(ProjectModel.kind)
        )
        return {kind: float(total) for kind, total in rows.all()}

    async def days_by_status(self, period: Period) -> dict[ProjectStatus, float]:
        rows = await self._session.execute(
            select(EntryModel.status_at_entry, func.sum(EntryModel.value))
            .where(and_(self._within(period), EntryModel.status_at_entry.is_not(None)))
            .group_by(EntryModel.status_at_entry)
        )
        return {status: float(total) for status, total in rows.all()}

    async def days_by_category(
        self, period: Period
    ) -> dict[ProjectCategory | None, float]:
        """Time per strategic axis, work packages counted with their parent.

        A work package carries no axis of its own: the axis is the parent
        project's, and leaving it out would hide part of what was spent on it.
        """
        parent = func.coalesce(ProjectModel.parent_id, ProjectModel.id)
        owner = select(ProjectModel.id, ProjectModel.category).subquery()
        rows = await self._session.execute(
            select(owner.c.category, func.sum(EntryModel.value))
            .select_from(EntryModel)
            .join(ProjectModel, ProjectModel.id == EntryModel.project_id)
            .join(owner, owner.c.id == parent)
            .where(self._within(period))
            .group_by(owner.c.category)
        )
        return {category: float(total) for category, total in rows.all()}

    async def top_missions(
        self, period: Period, limit: int
    ) -> list[tuple[int, str, float]]:
        total = func.sum(EntryModel.value)
        rows = await self._session.execute(
            select(ProjectModel.id, ProjectModel.label, total)
            .join(EntryModel, EntryModel.project_id == ProjectModel.id)
            .where(self._within(period))
            .group_by(ProjectModel.id, ProjectModel.label)
            .order_by(total.desc(), ProjectModel.label)
            .limit(limit)
        )
        return [(id_, label, float(days)) for id_, label, days in rows.all()]

    async def validated_months(self, months: list[date], user_ids: list[int]) -> int:
        if not months or not user_ids:
            return 0
        count = await self._session.scalar(
            select(func.count())
            .select_from(MonthModel)
            .where(
                and_(
                    MonthModel.month.in_(months),
                    MonthModel.user_id.in_(user_ids),
                    MonthModel.state == MonthState.VALIDATED,
                )
            )
        )
        return int(count or 0)

    async def active_missions(self) -> int:
        count = await self._session.scalar(
            select(func.count())
            .select_from(ProjectModel)
            .where(ProjectModel.is_active.is_(True))
        )
        return int(count or 0)

    async def active_missions_with_time(self, period: Period) -> int:
        count = await self._session.scalar(
            select(func.count(func.distinct(EntryModel.project_id)))
            .select_from(EntryModel)
            .join(ProjectModel, ProjectModel.id == EntryModel.project_id)
            .where(and_(self._within(period), ProjectModel.is_active.is_(True)))
        )
        return int(count or 0)

    async def missions_created(self, period: Period) -> int:
        """Missions added over the window, read from the trace of their birth.

        A project carries no creation date of its own; the audit log does, and
        it is the record that matters anyway.
        """
        count = await self._session.scalar(
            select(func.count())
            .select_from(AuditLogModel)
            .where(
                and_(
                    AuditLogModel.action == AuditAction.PROJECT_CREATE,
                    func.date(AuditLogModel.at).between(period.start, period.end),
                )
            )
        )
        return int(count or 0)
