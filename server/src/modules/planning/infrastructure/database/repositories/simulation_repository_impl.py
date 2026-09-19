"""SQLAlchemy implementation of the SimulationRepository port."""

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.planning.domain.entities.simulation import Simulation
from src.modules.planning.domain.repositories.simulation_repository import (
    SimulationRepository,
)
from src.modules.planning.infrastructure.database.models.simulation_model import (
    SimulationModel,
)


def to_entity(model: SimulationModel) -> Simulation:
    return Simulation(
        id=model.id,
        name=model.name,
        horizon_months=model.horizon_months,
        order=[int(project_id) for project_id in model.mission_order or []],
        # JSON object keys come back as strings whatever went in.
        staffing={
            int(project_id): [int(user_id) for user_id in user_ids]
            for project_id, user_ids in (model.staffing or {}).items()
        },
        author_id=model.author_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlSimulationRepository(SimulationRepository):
    """Persists saved scenarios."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Simulation]:
        # The newest id breaks a tie on the stamp. Postgres `now()` is the
        # transaction's clock, not the statement's: two scenarios touched in
        # one request carry the same stamp, and without this the list would
        # reshuffle itself between two identical reads.
        result = await self._session.execute(
            select(SimulationModel).order_by(
                SimulationModel.updated_at.desc(), SimulationModel.id.desc()
            )
        )
        return [to_entity(model) for model in result.scalars().all()]

    async def get_by_id(self, simulation_id: int) -> Simulation | None:
        model = await self._session.get(SimulationModel, simulation_id)
        return to_entity(model) if model else None

    async def find_by_name(self, name: str) -> Simulation | None:
        result = await self._session.execute(
            select(SimulationModel).where(
                func.lower(SimulationModel.name) == name.strip().lower()
            )
        )
        model = result.scalars().first()
        return to_entity(model) if model else None

    async def add(self, simulation: Simulation) -> Simulation:
        model = SimulationModel(
            name=simulation.name,
            horizon_months=simulation.horizon_months,
            mission_order=list(simulation.order),
            staffing={str(k): list(v) for k, v in simulation.staffing.items()},
            author_id=simulation.author_id,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return to_entity(model)

    async def update(self, simulation: Simulation) -> Simulation:
        model = await self._session.get(SimulationModel, simulation.id)
        if model is None:
            return simulation

        model.name = simulation.name
        model.horizon_months = simulation.horizon_months
        model.mission_order = list(simulation.order)
        model.staffing = {str(k): list(v) for k, v in simulation.staffing.items()}
        await self._session.flush()
        await self._session.refresh(model)
        return to_entity(model)

    async def delete(self, simulation_id: int) -> None:
        await self._session.execute(
            delete(SimulationModel).where(SimulationModel.id == simulation_id)
        )
