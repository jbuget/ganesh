"""A reaction left on an update."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Reaction(StrEnum):
    """What one may answer without writing a word.

    The set is closed on purpose. A reaction says « lu », « d'accord » or
    « bravo », and a thread where everyone invents their own sign says nothing
    at a glance; a closed set also spares the domain the job of deciding what
    counts as an emoji. Adding one is a decision taken here, not a keystroke
    taken in a picker.

    The order of the members is the order the bar is drawn in.
    """

    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    LAUGH = "laugh"
    HOORAY = "hooray"
    CONFUSED = "confused"
    HEART = "heart"
    ROCKET = "rocket"
    EYES = "eyes"


@dataclass(frozen=True)
class UpdateReaction:
    """One person, one sign, on one update.

    The same person may leave several signs on the same update, but never the
    same one twice: reacting again is how one takes it back.
    """

    update_id: int
    user_id: int
    reaction: Reaction
    at: datetime
