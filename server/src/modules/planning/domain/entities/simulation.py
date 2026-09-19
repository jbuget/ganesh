"""A scenario somebody kept.

A projection answers « et si ? » for as long as one is looking at it. A
simulation is the same question written down: the order one wanted to try and
who one wanted on what, named, so the conversation can be picked up next week
rather than retyped.

It stores a hypothesis and never a result. Dates are not kept: what a scenario
would cost depends on what has been declared since, and a landing date frozen
in a row would be a lie by the following Monday.
"""

from dataclasses import dataclass, field
from datetime import datetime

from src.modules.planning.domain.services.horizon import (
    DEFAULT_HORIZON_MONTHS,
    MAX_HORIZON_MONTHS,
)
from src.shared.exceptions.domain_exceptions import ValidationError

#: Long enough for « Priorité bailleurs, Valentin sur le portail ».
NAME_MAX_LENGTH = 80


@dataclass
class Simulation:
    """A named hypothesis on the plan: an order to serve, and who carries what."""

    id: int | None
    name: str
    horizon_months: int = DEFAULT_HORIZON_MONTHS
    #: Missions to serve first, in this order. What it leaves out follows in
    #: the order the board already tells.
    order: list[int] = field(default_factory=list)
    #: Who to place the work on, per mission. A mission absent from the map
    #: keeps the team it actually has.
    staffing: dict[int, list[int]] = field(default_factory=dict)
    #: Who wrote it down. Null once that account is gone: the scenario stays,
    #: the team is what owns it.
    author_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        if not self.name:
            raise ValidationError("A simulation must be named.")
        if len(self.name) > NAME_MAX_LENGTH:
            raise ValidationError(
                f"A simulation name runs to {NAME_MAX_LENGTH} characters at most."
            )
        if not 1 <= self.horizon_months <= MAX_HORIZON_MONTHS:
            raise ValidationError(
                f"A horizon runs from 1 to {MAX_HORIZON_MONTHS} months, "
                f"not {self.horizon_months}."
            )

    @property
    def is_empty(self) -> bool:
        """Whether it supposes anything at all.

        A simulation that supposes nothing is the team's own plan under another
        name: worth keeping if someone chose to, but it must not read as a
        hypothesis on the screen.
        """
        return not self.order and not self.staffing

    def restate(
        self,
        name: str,
        horizon_months: int,
        order: list[int],
        staffing: dict[int, list[int]],
    ) -> None:
        """Rewrites the scenario in place, keeping who first wrote it down."""
        self.name = name
        self.horizon_months = horizon_months
        self.order = order
        self.staffing = staffing
        self.__post_init__()
