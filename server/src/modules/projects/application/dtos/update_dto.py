"""Commands for a mission's follow-up thread."""

from dataclasses import dataclass

from src.modules.projects.domain.entities.update_reaction import Reaction


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


@dataclass(frozen=True)
class ReactCommand:
    """Leaving a sign under an update, or taking it back.

    The same command carries both gestures: a withdrawal names the sign it
    takes back, and names it for its own author alone.
    """

    actor_id: int
    update_id: int
    reaction: Reaction
