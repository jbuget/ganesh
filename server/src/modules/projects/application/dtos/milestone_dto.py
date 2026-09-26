"""Commands that change the dates a mission answers for."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class CreateMilestoneCommand:
    """Request to post a date on a mission."""

    actor_id: int
    project_id: int
    label: str
    expected_on: date
    reached_on: date | None = None


@dataclass(frozen=True)
class UpdateMilestoneCommand:
    """Request to change what a milestone says.

    Every field is optional and only what is named is written: marking one
    reached must not blank the label beside it. `reached_on` is not told apart
    from « leave as is » by its value — null is what takes a milestone back to
    unreached — but by whether it was named at all.
    """

    actor_id: int
    milestone_id: int
    label: str | None = None
    expected_on: date | None = None
    reached_on: date | None = None
    sets_reached_on: bool = False


@dataclass(frozen=True)
class DeleteMilestoneCommand:
    """Request to withdraw a date from a mission."""

    actor_id: int
    milestone_id: int
