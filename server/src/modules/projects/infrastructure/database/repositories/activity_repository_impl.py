"""Persistence of the activities a mission is cut into."""

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.entries.infrastructure.database.models.entry_model import EntryModel
from src.modules.projects.domain.entities.activity import Activity
from src.modules.projects.domain.repositories.activity_repository import (
    ActivityRepository,
)
from src.modules.projects.infrastructure.database.models.activity_model import (
    ActivityModel,
)


def _to_entity(model: ActivityModel) -> Activity:
    return Activity(
        id=model.id,
        project_id=model.project_id,
        label=model.label,
        nature=model.nature,
        estimated_days=model.estimated_days,
        is_active=model.is_active,
        archived_at=model.archived_at,
    )


class SqlActivityRepository(ActivityRepository):
    """Activities stored in their own table."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, activity: Activity) -> Activity:
        model = ActivityModel(
            project_id=activity.project_id,
            label=activity.label,
            nature=activity.nature,
            estimated_days=activity.estimated_days,
            is_active=activity.is_active,
            archived_at=activity.archived_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def get_by_id(self, activity_id: int) -> Activity | None:
        model = await self._session.get(ActivityModel, activity_id)
        return _to_entity(model) if model else None

    async def update(self, activity: Activity) -> Activity:
        model = await self._session.get(ActivityModel, activity.id)
        if model is None:
            raise ValueError(f"No activity with id {activity.id}.")

        model.label = activity.label
        model.nature = activity.nature
        model.estimated_days = activity.estimated_days
        model.is_active = activity.is_active
        model.archived_at = activity.archived_at
        await self._session.flush()
        return _to_entity(model)

    async def list_for_project(self, project_id: int) -> list[Activity]:
        result = await self._session.execute(
            select(ActivityModel)
            .where(ActivityModel.project_id == project_id)
            .order_by(ActivityModel.label)
        )
        return [_to_entity(model) for model in result.scalars().all()]

    async def list_for_projects(
        self, project_ids: Sequence[int]
    ) -> dict[int, list[Activity]]:
        if not project_ids:
            return {}

        result = await self._session.execute(
            select(ActivityModel)
            .where(ActivityModel.project_id.in_(project_ids))
            .order_by(ActivityModel.label)
        )

        by_project: dict[int, list[Activity]] = {}
        for model in result.scalars().all():
            by_project.setdefault(model.project_id, []).append(_to_entity(model))
        return by_project

    async def count_entries(self, activity_id: int) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(EntryModel)
            .where(EntryModel.activity_id == activity_id)
        )
        return int(result.scalar_one())
