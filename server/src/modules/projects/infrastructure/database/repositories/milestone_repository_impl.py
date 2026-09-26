"""Persistence of the dates a mission answers for."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.projects.domain.entities.milestone import Milestone
from src.modules.projects.domain.repositories.milestone_repository import (
    MilestoneRepository,
)
from src.modules.projects.infrastructure.database.models.milestone_model import (
    MilestoneModel,
)


def _to_entity(model: MilestoneModel) -> Milestone:
    return Milestone(
        id=model.id,
        project_id=model.project_id,
        label=model.label,
        expected_on=model.expected_on,
        reached_on=model.reached_on,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlMilestoneRepository(MilestoneRepository):
    """Milestones stored in their own table."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, milestone: Milestone) -> Milestone:
        model = MilestoneModel(
            project_id=milestone.project_id,
            label=milestone.label,
            expected_on=milestone.expected_on,
            reached_on=milestone.reached_on,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def get_by_id(self, milestone_id: int) -> Milestone | None:
        model = await self._session.get(MilestoneModel, milestone_id)
        return _to_entity(model) if model else None

    async def update(self, milestone: Milestone) -> Milestone:
        model = await self._session.get(MilestoneModel, milestone.id)
        if model is None:
            raise ValueError(f"No milestone with id {milestone.id}.")

        model.label = milestone.label
        model.expected_on = milestone.expected_on
        model.reached_on = milestone.reached_on
        await self._session.flush()
        # Read back rather than taken as it stands: `updated_at` is written by
        # the column, so the flush leaves it expired. Reading an expired
        # attribute loads it lazily, which in async is not a load but a
        # crash — and the screen would get a 500 where it asked for a date.
        await self._session.refresh(model)
        return _to_entity(model)

    async def list_for_project(self, project_id: int) -> list[Milestone]:
        result = await self._session.execute(
            select(MilestoneModel).where(MilestoneModel.project_id == project_id)
            # The id breaks a tie so that two milestones announced for the
            # same day keep a stable order from one reading to the next.
            .order_by(MilestoneModel.expected_on, MilestoneModel.id)
        )
        return [_to_entity(model) for model in result.scalars().all()]

    async def delete(self, milestone_id: int) -> None:
        model = await self._session.get(MilestoneModel, milestone_id)
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()
