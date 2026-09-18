"""Commands for a mission's follow-up thread."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PostUpdateCommand:
    """Posting an update."""

    actor_id: int
    project_id: int
    body: str


@dataclass(frozen=True)
class EditUpdateCommand:
    """Correcting an update already posted."""

    actor_id: int
    update_id: int
    body: str


@dataclass(frozen=True)
class RemoveUpdateCommand:
    """Withdrawing an update."""

    actor_id: int
    update_id: int
