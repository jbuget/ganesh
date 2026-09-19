"""Keeping, listing, rewriting and dropping the scenarios the team saved.

One class per intention rather than one that does everything: each says in its
name what it is allowed to do, and none of them can quietly grow a second job.
"""

from dataclasses import dataclass, field

from src.modules.planning.domain.entities.simulation import Simulation
from src.modules.planning.domain.repositories.simulation_repository import (
    SimulationRepository,
)
from src.shared.exceptions.domain_exceptions import ConflictError, EntityNotFoundError


@dataclass(frozen=True)
class SimulationCommand:
    """A scenario to write down, as it comes off the screen."""

    name: str
    horizon_months: int
    order: list[int] = field(default_factory=list)
    staffing: dict[int, list[int]] = field(default_factory=dict)


class ListSimulationsUseCase:
    """Every scenario the team kept, most recently touched first."""

    def __init__(self, simulations: SimulationRepository) -> None:
        self._simulations = simulations

    async def execute(self) -> list[Simulation]:
        return await self._simulations.list_all()


class SaveSimulationUseCase:
    """Writes a scenario down under a name nobody else is using."""

    def __init__(self, simulations: SimulationRepository) -> None:
        self._simulations = simulations

    async def execute(self, command: SimulationCommand, author_id: int) -> Simulation:
        await _refuse_a_taken_name(self._simulations, command.name, keeping=None)

        return await self._simulations.add(
            Simulation(
                id=None,
                name=command.name,
                horizon_months=command.horizon_months,
                order=command.order,
                staffing=command.staffing,
                author_id=author_id,
            )
        )


class UpdateSimulationUseCase:
    """Rewrites a scenario in place, so trying again costs no second row."""

    def __init__(self, simulations: SimulationRepository) -> None:
        self._simulations = simulations

    async def execute(
        self, simulation_id: int, command: SimulationCommand
    ) -> Simulation:
        simulation = await self._simulations.get_by_id(simulation_id)
        if simulation is None:
            raise EntityNotFoundError("The simulation cannot be found.")

        await _refuse_a_taken_name(
            self._simulations, command.name, keeping=simulation_id
        )

        simulation.restate(
            name=command.name,
            horizon_months=command.horizon_months,
            order=command.order,
            staffing=command.staffing,
        )
        return await self._simulations.update(simulation)


class DeleteSimulationUseCase:
    """Drops a scenario.

    Anyone may, as anyone may move a card on the board: a simulation holds no
    declared time and changes nothing that was decided. Trust is the stance
    here too.
    """

    def __init__(self, simulations: SimulationRepository) -> None:
        self._simulations = simulations

    async def execute(self, simulation_id: int) -> None:
        simulation = await self._simulations.get_by_id(simulation_id)
        if simulation is None:
            raise EntityNotFoundError("The simulation cannot be found.")

        await self._simulations.delete(simulation_id)


async def _refuse_a_taken_name(
    simulations: SimulationRepository, name: str, keeping: int | None
) -> None:
    """Two scenarios of the same name would make choosing one a guess."""
    existing = await simulations.find_by_name(name.strip())
    if existing is not None and existing.id != keeping:
        raise ConflictError(f"A simulation is already named « {name.strip()} ».")
