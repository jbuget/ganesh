"""Everything one numéro of the gazette is made of, before it is written.

The brief is the whole of what the gazette knows. A chapeau may be laid over
it afterwards, and may fail to be: the numéro is the brief, never the prose.
"""

from dataclasses import dataclass, field
from datetime import date

from src.modules.gazette.domain.entities.highlight import Highlight
from src.modules.gazette.domain.entities.movement import Movement


@dataclass(frozen=True)
class Tally:
    """What the month came to, in figures.

    Every figure is an aggregate and names nobody. Singling a teammate out in
    a count is not measuring, it is pointing — and the month after, nobody
    fills anything in.
    """

    projects_created: int = 0
    projects_archived: int = 0
    phase_changes: int = 0
    news_posted: int = 0
    months_validated: int = 0
    #: What the company asked for, and what became a mission. Two figures
    #: rather than one: what is asked and what is built are two facts, and a
    #: month that filed six and built none says something either alone hides.
    requests_filed: int = 0
    requests_converted: int = 0


@dataclass(frozen=True)
class Brief:
    """One month of the register, read back."""

    month: date
    tally: Tally
    movements: list[Movement] = field(default_factory=list)
    highlights: list[Highlight] = field(default_factory=list)
