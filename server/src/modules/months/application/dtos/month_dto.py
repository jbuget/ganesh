"""Commands acting on the state of a month."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ValidateMonthCommand:
    """Request to validate a month. Everyone validates their own."""

    actor_id: int
    target_user_id: int
    month: date


@dataclass(frozen=True)
class ReopenMonthCommand:
    """Request to reopen a validated month. Managers only."""

    actor_id: int
    target_user_id: int
    month: date
