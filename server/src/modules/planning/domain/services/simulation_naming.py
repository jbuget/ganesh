"""What a simulation may be called.

The rule is shared by writing a scenario down and by rewriting one, and a use
case may never lean on another: it belongs here, where both can reach it and
neither owns it.
"""

from src.modules.planning.domain.repositories.simulation_repository import (
    SimulationRepository,
)
from src.shared.exceptions.domain_exceptions import ConflictError


async def ensure_name_is_free(
    simulations: SimulationRepository, name: str, keeping: int | None = None
) -> None:
    """Refuses a name another scenario already bears.

    Two scenarios called « Priorité bailleurs » would make choosing between
    them a guess, which is the opposite of what a saved hypothesis is for.

    `keeping` is the scenario being rewritten: a scenario keeping its own name
    clashes with nothing.
    """
    taken = name.strip()
    existing = await simulations.find_by_name(taken)
    if existing is not None and existing.id != keeping:
        raise ConflictError(f"A simulation is already named « {taken} ».")
