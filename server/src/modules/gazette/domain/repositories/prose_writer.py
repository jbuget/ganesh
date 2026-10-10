"""Port for what a machine writes over a month.

The port hands over a dossier and takes back a narrative, and what a narrative
may hold is decided by the domain: no implementation can widen it. A writer
that is not configured, that times out, or that writes something that does not
hold all answer the same way — nothing — and the numéro goes out on its facts
alone.
"""

from abc import ABC, abstractmethod

from src.modules.gazette.domain.entities.dossier import Dossier
from src.modules.gazette.domain.entities.narrative import Narrative


class ProseWriter(ABC):
    """Writes the editorial and the spotlights laid over a month's facts."""

    @abstractmethod
    async def write(self, dossier: Dossier) -> Narrative:
        """What the model wrote that holds, which may be nothing at all."""
        ...
