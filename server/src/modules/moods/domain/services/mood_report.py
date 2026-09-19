"""What the team's morale reads like over a window of days."""

from dataclasses import dataclass
from datetime import date

from src.modules.moods.domain.entities.mood import Mood, MoodLevel


@dataclass(frozen=True)
class SignedMood:
    """A mood and who posted it.

    The team screen names everyone: the mood is attached to a person on
    purpose, and nothing here pretends otherwise.
    """

    user_id: int
    level: MoodLevel


@dataclass(frozen=True)
class DayMoods:
    """One day of the window, and what the team said of it."""

    day: date
    #: Worst first, as the scale itself runs: what makes the shape of a day
    #: readable at a glance is that it always climbs the same way.
    moods: tuple[SignedMood, ...]

    @property
    def participation(self) -> int:
        """How many answered."""
        return len(self.moods)

    @property
    def average(self) -> float | None:
        """The mean of the answers, or None when there are none.

        It weighs the answers alone, never the silences: a day three people
        out of fifteen answered says what those three felt, and a mean that
        counted the twelve others as neutral would invent their day.
        """
        if not self.moods:
            return None
        return round(
            sum(signed.level.score for signed in self.moods) / len(self.moods), 2
        )

    @property
    def counts(self) -> dict[MoodLevel, int]:
        """How many of each level, every level named even at zero.

        A level missing from the mapping and a level at zero read the same on
        a stacked bar, and the first would leave a hole in the legend.
        """
        return {
            level: sum(1 for signed in self.moods if signed.level is level)
            for level in MoodLevel
        }


@dataclass(frozen=True)
class MoodReport:
    """The window the team screen draws."""

    #: The most recent day first.
    days: tuple[DayMoods, ...]
    #: Active teammates, against which participation is read.
    headcount: int


def build_report(days: list[date], moods: list[Mood], headcount: int) -> MoodReport:
    """Lays the moods out over the days of the window.

    A day the window does not hold is dropped rather than added: the window is
    what the caller asked for, and a mood posted outside it belongs to another
    reading.
    """
    by_day: dict[date, list[Mood]] = {day: [] for day in days}
    for mood in moods:
        if mood.day in by_day:
            by_day[mood.day].append(mood)

    return MoodReport(
        days=tuple(
            DayMoods(
                day=day,
                moods=tuple(
                    SignedMood(user_id=mood.user_id, level=mood.level)
                    for mood in sorted(
                        by_day[day], key=lambda m: (m.level.score, m.user_id)
                    )
                ),
            )
            for day in days
        ),
        headcount=headcount,
    )
