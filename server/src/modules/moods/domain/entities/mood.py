"""How a day felt, for one teammate."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class MoodLevel(StrEnum):
    """How a day felt, from the worst to the best.

    The order declared here is the order the choices are offered in, the order
    a day's answers lay out, and the order a stacked bar is read in. A scale
    climbs: it runs low to high, as any axis does, and having it climb in one
    place and fall in another would make the same five faces read twice.
    """

    BAD = "bad"
    HARD = "hard"
    NEUTRAL = "neutral"
    GOOD = "good"
    EXCELLENT = "excellent"

    @property
    def score(self) -> int:
        """Where the level sits on the scale: 1 for the worst, 5 for the best.

        Derived from the order above and never stored. What a teammate posts
        is a face, not a mark; the figure only exists to draw a trend, and
        keeping it out of the database is what stops it from becoming a note
        on a person.
        """
        return list(MoodLevel).index(self) + 1


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
