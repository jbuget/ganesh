"""Keeping, listing, rewriting and dropping the scenarios the team saved.

One class per intention rather than one that does everything: each says in its
name what it is allowed to do, and none of them can quietly grow a second job.
"""

from dataclasses import dataclass, field

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.planning.domain.entities.simulation import Simulation
from src.modules.planning.domain.repositories.simulation_repository import (
    SimulationRepository,
)
from src.modules.planning.domain.services.simulation_naming import ensure_name_is_free
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


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


async def _trace_simulation(
    audit_logs: AuditLogRepository,
    action: AuditAction,
    actor_id: int,
    simulation: Simulation,
) -> None:
    """Records a scenario being kept, rewritten or dropped.

    A simulation is thrown away by design, and carries no project: its lines
    live in the table alone, under nobody's log. They are still worth writing —
    a scenario staffs people, and who asked that question, and when, is the
    kind of thing one comes back to.
    """
    await audit_logs.add(
        AuditLog(
            action=action,
            actor_id=actor_id,
            new_value=simulation.name,
            payload={"simulation_id": simulation.id},
        )
    )


class SaveSimulationUseCase:
    """Writes a scenario down under a name nobody else is using."""

    def __init__(
        self, simulations: SimulationRepository, audit_logs: AuditLogRepository
    ) -> None:
        self._simulations = simulations
        self._audit_logs = audit_logs

    async def execute(self, command: SimulationCommand, author_id: int) -> Simulation:
        await ensure_name_is_free(self._simulations, command.name)

        saved = await self._simulations.add(
            Simulation(
                id=None,
                name=command.name,
                horizon_months=command.horizon_months,
                order=command.order,
                staffing=command.staffing,
                author_id=author_id,
            )
        )
        await _trace_simulation(
            self._audit_logs, AuditAction.SIMULATION_CREATE, author_id, saved
        )
        return saved


class UpdateSimulationUseCase:
    """Rewrites a scenario in place, so trying again costs no second row."""

    def __init__(
        self, simulations: SimulationRepository, audit_logs: AuditLogRepository
    ) -> None:
        self._simulations = simulations
        self._audit_logs = audit_logs

    async def execute(
        self, simulation_id: int, command: SimulationCommand, actor_id: int
    ) -> Simulation:
        simulation = await self._simulations.get_by_id(simulation_id)
        if simulation is None:
            raise EntityNotFoundError("The simulation cannot be found.")

        await ensure_name_is_free(
            self._simulations, command.name, keeping=simulation_id
        )

        simulation.restate(
            name=command.name,
            horizon_months=command.horizon_months,
            order=command.order,
            staffing=command.staffing,
        )
        rewritten = await self._simulations.update(simulation)
        await _trace_simulation(
            self._audit_logs, AuditAction.SIMULATION_UPDATE, actor_id, rewritten
        )
        return rewritten


class DeleteSimulationUseCase:
    """Drops a scenario.

    Anyone may, as anyone may move a card on the board: a simulation holds no
    declared time and changes nothing that was decided. Trust is the stance
    here too.
    """

    def __init__(
        self, simulations: SimulationRepository, audit_logs: AuditLogRepository
    ) -> None:
        self._simulations = simulations
        self._audit_logs = audit_logs

    async def execute(self, simulation_id: int, actor_id: int) -> None:
        simulation = await self._simulations.get_by_id(simulation_id)
        if simulation is None:
            raise EntityNotFoundError("The simulation cannot be found.")

        await self._simulations.delete(simulation_id)
        await _trace_simulation(
            self._audit_logs, AuditAction.SIMULATION_DELETE, actor_id, simulation
        )
