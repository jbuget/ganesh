"""How a day felt, for one teammate."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class MoodLevel(StrEnum):
    """How a day felt, from the best to the worst.

    The order declared here is the order the choices are offered in, and the
    order a day's moods are read in.
    """

    EXCELLENT = "excellent"
    GOOD = "good"
    NEUTRAL = "neutral"
    HARD = "hard"
    BAD = "bad"

    @property
    def score(self) -> int:
        """Where the level sits on the scale: 5 for the best, 1 for the worst.

        Derived from the order above and never stored. What a teammate posts
        is a face, not a mark; the figure only exists to draw a trend, and
        keeping it out of the database is what stops it from becoming a note
        on a person.
        """
        return len(MoodLevel) - list(MoodLevel).index(self)


@dataclass
class Mood:
    """The mood a teammate posted on a day.

    One per person and per day: posting again changes the first one rather
    than adding to it.
    """

    id: int | None
    user_id: int
    day: date
    level: MoodLevel
