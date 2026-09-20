"""Port for the one thing in the gazette a machine writes.

The port hands over a brief and takes back a chapeau, never a figure: what a
`Prose` may hold is decided by the domain, and no implementation can widen it.
A writer that is not configured, that times out, or that writes something
carrying a count all answer the same way — nothing — and the numéro goes out
on its facts alone.
"""

from abc import ABC, abstractmethod

from src.modules.gazette.domain.entities.brief import Brief
from src.modules.gazette.domain.entities.prose import Prose


class ProseWriter(ABC):
    """Writes the chapeau laid over a month's facts."""

    @abstractmethod
    async def write(self, brief: Brief) -> Prose | None:
        """A few sentences over the month, or nothing at all."""
        ...
