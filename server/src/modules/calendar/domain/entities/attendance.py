"""The days somebody says they will be there, and what is supposed beyond them.

A rhythm is a rule — « four days a week, never on Wednesdays » — and a rule
applied to days needs a date it takes effect on, a successor, an order of
precedence. Attendance is the other way round: a day carries its own value,
and nothing is declared about days in general.

Two consequences the whole design rests on:

- **The past is not rewritten.** One enters the weeks to come, so what was
  already read stays as it was read. No date of effect, and nothing to
  correct in the past by accident.
- **What is not entered is supposed, and said to be.** Entry covers a month;
  Planification reads twelve. Beyond the entries, the habit of the last weeks
  holds — read, never declared, so nobody is asked to keep a rule up to date
  alongside their days.
"""

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, timedelta

from src.modules.calendar.domain.entities.week_pattern import (
    FULL_TIME,
    WEEKDAYS,
    WeekPattern,
)
from src.modules.calendar.domain.services.working_days import DayKind, classify_day

#: Weeks read to tell a habit from a day off. Four covers a month, which is
#: also what one enters at a time: the habit is read off what was just said.
WEEKS_READ = 4


def _monday_of(day: date) -> date:
    return day - timedelta(days=day.weekday())


def habit_of(entered: Mapping[date, float], weeks: int = WEEKS_READ) -> WeekPattern:
    """What the last weeks entered say an ordinary week looks like.

    Read rather than declared: nobody is asked to keep a rule up to date
    beside their days, and a habit that no longer matches what somebody
    enters corrects itself the following week.

    The majority of the weeks read decides each day, so one Thursday taken
    off is a day off and four of them are a rhythm. A tie follows the most
    recent weeks: two and two means somebody is changing their days, and it
    is the change that the weeks to come will look like.
    """
    if not entered:
        return FULL_TIME

    last_monday = _monday_of(max(entered))
    opens_on = last_monday - timedelta(weeks=weeks - 1)

    seen: dict[int, list[tuple[date, float]]] = {index: [] for index in range(5)}
    for day, value in sorted(entered.items()):
        if day >= opens_on and day.weekday() < len(WEEKDAYS):
            seen[day.weekday()].append((day, value))

    ordinary: dict[str, float] = {}
    for index, name in enumerate(WEEKDAYS):
        ordinary[name] = _usual(seen[index])
    return WeekPattern(**ordinary)


def _usual(days: list[tuple[date, float]]) -> float:
    """The value a day of the week usually holds, ties going to the latest."""
    if not days:
        return 1.0

    counted = Counter(value for _, value in days)
    most = max(counted.values())
    tied = {value for value, times in counted.items() if times == most}
    if len(tied) == 1:
        return tied.pop()
    return next(value for _, value in reversed(days) if value in tied)


@dataclass(frozen=True)
class Attendance:
    """One person's days: those entered, and the habit that covers the rest."""

    _entered: Mapping[date, float]
    habit: WeekPattern

    @classmethod
    def of(cls, entered: Mapping[date, float]) -> "Attendance":
        return cls(dict(entered), habit_of(entered))

    def was_entered(self, day: date) -> bool:
        """Whether this day is a fact or a supposition.

        A screen draws the two differently, as the roadmap already draws what
        was lived apart from what is merely projected.
        """
        return day in self._entered

    def on(self, day: date) -> float:
        """What this person is expected to work that day.

        Nothing at a weekend or on a public holiday, whatever was entered:
        that is an invariant of the domain, not a matter of attendance.

        Before the first entry, full time — what the application assumed of
        everybody before attendance existed, so no figure already read moves.
        """
        if classify_day(day) is not DayKind.WORKING:
            return 0.0
        if day in self._entered:
            return self._entered[day]
        if self._entered and day < min(self._entered):
            return 1.0
        return self.habit.on(day)
