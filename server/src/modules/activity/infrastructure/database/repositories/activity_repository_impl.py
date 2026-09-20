"""SQLAlchemy implementation of the ActivityRepository port."""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.activity.domain.repositories.activity_repository import (
    ActivityRepository,
    DeclaredDays,
    MissionRecord,
)
from src.modules.calendar.domain.entities.period import Period
from src.modules.entries.infrastructure.database.models.entry_model import EntryModel
from src.modules.projects.infrastructure.database.models.project_model import (
    ProjectModel,
)


class SqlActivityRepository(ActivityRepository):
    """Groups the window straight in the database.

    The matrix is one `GROUP BY project_id, user_id` and nothing more: no
    caller ever walks a list of entries to fill a cell.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def declared_days(self, period: Period) -> list[DeclaredDays]:
        rows = await self._session.execute(
            select(
                EntryModel.project_id,
                EntryModel.user_id,
                func.sum(EntryModel.value),
            )
            .where(EntryModel.day.between(period.start, period.end))
            .group_by(EntryModel.project_id, EntryModel.user_id)
        )
        return [
            DeclaredDays(project_id=project_id, user_id=user_id, days=float(days))
            for project_id, user_id, days in rows.all()
        ]

    async def missions_touched(self, period: Period) -> list[MissionRecord]:
        touched = (
            select(EntryModel.project_id)
            .where(EntryModel.day.between(period.start, period.end))
            .distinct()
            .scalar_subquery()
        )
        # Parents come along even when they received nothing themselves: a
        # work package rolls up into its project, and a project with no label
        # to roll into would leave the package stranded at the top level.
        parents = (
            select(ProjectModel.parent_id)
            .where(ProjectModel.id.in_(touched), ProjectModel.parent_id.is_not(None))
            .distinct()
            .scalar_subquery()
        )
        rows = await self._session.execute(
            select(ProjectModel).where(
                or_(ProjectModel.id.in_(touched), ProjectModel.id.in_(parents))
            )
        )
        return [
            MissionRecord(
                project_id=project.id,
                label=project.label,
                kind=project.kind,
                status=project.status,
                category=project.category,
                parent_id=project.parent_id,
            )
            for project in rows.scalars().all()
        ]

    async def days_by_mission(self, period: Period) -> dict[int, float]:
        rows = await self._session.execute(
            select(EntryModel.project_id, func.sum(EntryModel.value))
            .where(EntryModel.day.between(period.start, period.end))
            .group_by(EntryModel.project_id)
        )
        return {project_id: float(days) for project_id, days in rows.all()}
