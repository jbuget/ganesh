"""How much of a week a teammate works, and since when.

A rhythm is declared, never deduced, and it is never edited: one declares a
new one beside the last. A coverage read over March must be read with what
March knew — rewriting the motif in September would silently move every
figure ever computed about the spring.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date

from src.modules.calendar.domain.entities.week_pattern import FULL_TIME, WeekPattern


@dataclass(frozen=True)
class Rhythm:
    """A week motif, from the day it took effect."""

    id: int | None
    user_id: int
    pattern: WeekPattern
    effective_from: date


@dataclass(frozen=True)
class RhythmHistory:
    """Every rhythm one teammate declared, and what it expects of a day.

    `on()` is deliberately the same question a `WeekPattern` answers: a
    window's expectation is computed the same way whether it reads somebody
    who declared a rhythm or somebody who never did.
    """

    _declared: tuple[Rhythm, ...] = field(default_factory=tuple)

    @classmethod
    def of(cls, rhythms: Iterable[Rhythm]) -> "RhythmHistory":
        """Orders what was declared, oldest first, whatever order it came in."""
        return cls(tuple(sorted(rhythms, key=lambda one: one.effective_from)))

    def in_force_on(self, day: date) -> Rhythm | None:
        """The rhythm that holds that day, if one had been declared by then."""
        held: Rhythm | None = None
        for rhythm in self._declared:
            if rhythm.effective_from > day:
                break
            held = rhythm
        return held

    def next_after(self, day: date) -> Rhythm | None:
        """The nearest rhythm that has not opened yet, if one was declared.

        Told apart from what is in force so a screen can show both. Declaring
        a rhythm that opens next month is legitimate; a panel that showed only
        today's would send the declaration into a silence indistinguishable
        from a write that failed.
        """
        return next((one for one in self._declared if one.effective_from > day), None)

    def pattern_on(self, day: date) -> WeekPattern:
        """The motif in force that day.

        Full time until the first one was declared: that is what the
        application assumed of everybody before rhythms existed, so declaring
        one moves nothing that came before it.
        """
        held = self.in_force_on(day)
        return held.pattern if held else FULL_TIME

    def on(self, day: date) -> float:
        """Days this teammate is expected to work on this day."""
        return self.pattern_on(day).on(day)

    @property
    def latest(self) -> Rhythm | None:
        """The last one declared, by date of effect.

        Told apart from what is in force today on purpose: one may declare a
        rhythm that opens next month, and a screen that showed it as the
        current one would say somebody is already at four fifths when they
        are not. What holds today is `pattern_on(today)`.
        """
        return self._declared[-1] if self._declared else None
