"""Port for the simulations the team keeps."""

from abc import ABC, abstractmethod

from src.modules.planning.domain.entities.simulation import Simulation


class SimulationRepository(ABC):
    """Persistence contract for saved scenarios."""

    @abstractmethod
    async def list_all(self) -> list[Simulation]:
        """Every simulation, most recently touched first.

        Scenarios come back whole rather than as a list of names: they hold a
        handful of numbers each, and selecting one must not cost a second
        round trip before the plan can be redrawn.
        """
        ...

    @abstractmethod
    async def get_by_id(self, simulation_id: int) -> Simulation | None: ...

    @abstractmethod
    async def find_by_name(self, name: str) -> Simulation | None:
        """The simulation bearing this name, whatever its casing.

        Two scenarios called « Priorité bailleurs » would make choosing one a
        guess, which is the opposite of what a saved hypothesis is for.
        """
        ...

    @abstractmethod
    async def add(self, simulation: Simulation) -> Simulation: ...

    @abstractmethod
    async def update(self, simulation: Simulation) -> Simulation: ...

    @abstractmethod
    async def delete(self, simulation_id: int) -> None: ...
