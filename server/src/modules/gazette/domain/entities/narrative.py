"""Everything a model wrote over one month: the editorial and the spotlights."""

from dataclasses import dataclass

from src.modules.gazette.domain.entities.prose import Prose
from src.modules.gazette.domain.entities.spotlight import Spotlight


@dataclass(frozen=True)
class Narrative:
    """What was written, and held. Either part may be missing.

    A model that is down, slow or wrong costs the numéro its prose and never
    its month: an empty narrative is a normal outcome.
    """

    editorial: Prose | None = None
    spotlights: tuple[Spotlight, ...] = ()
