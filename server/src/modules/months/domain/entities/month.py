"""Entry state of a month for a given user."""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum

from src.modules.months.domain.services.month_period import first_day_of
from src.modules.users.domain.entities.user import User
from src.shared.exceptions.domain_exceptions import ForbiddenActionError
from src.shared.utils import clock


class MonthState(StrEnum):
    """Entry state of a month."""

    OPEN = "open"
    VALIDATED = "validated"


@dataclass
class Month:
    """A month of entries, for one user.

    A validated month is immutable: no write is possible until a manager
    reopens it. The discipline comes from the traceability of the move, not
    from a permanent lock.
    """

    user_id: int
    month: date
    state: MonthState = MonthState.OPEN
    validated_at: datetime | None = None
    validated_by: int | None = None
    reopened_at: datetime | None = None
    reopened_by: int | None = None
    id: int | None = field(default=None)

    def __post_init__(self) -> None:
        self.month = first_day_of(self.month)

    @property
    def is_writable(self) -> bool:
        """Only an open month accepts entries."""
        return self.state is MonthState.OPEN

    def validate(self, by: User, at: datetime | None = None) -> None:
        """Locks the month. Everyone validates their own."""
        if self.state is MonthState.VALIDATED:
            raise ForbiddenActionError("This month is already validated.")
        self.state = MonthState.VALIDATED
        self.validated_by = by.id
        self.validated_at = at or clock.now()

    def reopen(self, by: User, at: datetime | None = None) -> None:
        """Reopens a validated month. Managers only, and traced."""
        if self.state is not MonthState.VALIDATED:
            raise ForbiddenActionError(
                "This month is not validated, it is already open."
            )
        if not by.can_reopen_month():
            raise ForbiddenActionError(
                "Only a manager can reopen a validated month.",
            )
        self.state = MonthState.OPEN
        self.reopened_by = by.id
        self.reopened_at = at or clock.now()
