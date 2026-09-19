"""Commands that write entries."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SetEntryCommand:
    """Request to write an entry.

    `actor_id` is who acts, `target_user_id` whose month is changed. They
    differ when a colleague fixes an entry.
    """

    actor_id: int
    target_user_id: int
    project_id: int
    day: date
    value: float


@dataclass(frozen=True)
class ClearEntryCommand:
    """Request to delete an entry."""

    actor_id: int
    target_user_id: int
    project_id: int
    day: date


@dataclass(frozen=True)
class RemoveMissionCommand:
    """Request to remove a whole mission from a month.

    `month` may be any day of the month aimed at: only the month matters.
    """

    actor_id: int
    target_user_id: int
    project_id: int
    month: date


@dataclass(frozen=True)
class AddMissionCommand:
    """Request to put a mission on a month, before any time is entered on it.

    `month` may be any day of the month aimed at: only the month matters.
    """

    actor_id: int
    target_user_id: int
    project_id: int
    month: date
