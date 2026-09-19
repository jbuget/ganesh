"""Commands and readings of the mood module."""

from dataclasses import dataclass
from datetime import date

from src.modules.moods.domain.entities.mood import MoodLevel
from src.modules.moods.domain.services.mood_report import MoodReport
from src.modules.users.domain.entities.user import User


@dataclass(frozen=True)
class SetMoodCommand:
    """Request to post a mood, or to change the one already posted.

    Nobody posts for anybody else: unlike a month, which a colleague may fill
    in, a mood only has an author.
    """

    user_id: int
    day: date
    level: MoodLevel


@dataclass(frozen=True)
class OpenDay:
    """A day one may still answer for, and what one has already said of it."""

    day: date
    level: MoodLevel | None


@dataclass(frozen=True)
class TeamMoods:
    """The team window, and the people it names."""

    report: MoodReport
    people: list[User]
