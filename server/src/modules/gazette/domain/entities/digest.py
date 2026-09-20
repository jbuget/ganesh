"""A generated digest: one month of the register, as it read that day.

A digest is never rewritten. Asking for the month again writes a new version
beside the old one, and the screen shows the latest. That is what makes the
facts safe to quote: a figure somebody read in a digest is still in it a year
later, even though the register has moved on since.
"""

from dataclasses import dataclass
from datetime import date, datetime

from src.modules.gazette.domain.entities.brief import Brief
from src.modules.gazette.domain.entities.prose import Prose
from src.shared.exceptions.domain_exceptions import ValidationError

#: What the first generation of a month is numbered.
FIRST_VERSION = 1


@dataclass(frozen=True)
class Digest:
    """One generation of one month."""

    month: date
    #: Which generation of that month this is, counted from one.
    version: int
    brief: Brief
    generated_at: datetime
    #: Who asked for it, as the reader names them. Anyone may: a digest reads
    #: a register the whole team already has open.
    requested_by: str
    #: What a model wrote over the facts, when it wrote something that held.
    #: A digest without it is a digest all the same.
    prose: Prose | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "requested_by", self.requested_by.strip())
        if not self.requested_by:
            raise ValidationError("A digest says who asked for it.")
        if self.version < FIRST_VERSION:
            raise ValidationError("A digest version is counted from one.")
        if self.month != self.brief.month:
            raise ValidationError("A digest covers the month its facts come from.")


@dataclass(frozen=True)
class DigestVersion:
    """One line of a month's history: enough to offer a version, not to read it."""

    version: int
    generated_at: datetime
    requested_by: str
