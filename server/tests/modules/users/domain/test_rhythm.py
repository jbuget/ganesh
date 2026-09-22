"""The rhythms a teammate has declared, and what each day expects of them."""

from datetime import date

from src.modules.calendar.domain.entities.week_pattern import FULL_TIME, WeekPattern
from src.modules.users.domain.entities.rhythm import Rhythm, RhythmHistory

MARCH = date(2026, 3, 1)
SEPTEMBER = date(2026, 9, 1)

# A Wednesday and the Thursday that follows it, in June.
WEDNESDAY = date(2026, 6, 17)
THURSDAY = date(2026, 6, 18)
SATURDAY = date(2026, 6, 20)

FOUR_FIFTHS = WeekPattern(wednesday=0.0)
HALF_TIME = WeekPattern(wednesday=0.0, thursday=0.0, friday=0.0)


def _declared(pattern: WeekPattern, effective_from: date) -> Rhythm:
    return Rhythm(id=None, user_id=1, pattern=pattern, effective_from=effective_from)


def test_somebody_who_declared_nothing_is_expected_full_time() -> None:
    # What the application assumed of everyone before rhythms existed: a
    # default that moves no figure is the only honest one.
    history = RhythmHistory.of([])

    assert history.pattern_on(WEDNESDAY) == FULL_TIME
    assert history.on(WEDNESDAY) == 1.0


def test_a_rhythm_applies_from_the_day_it_took_effect() -> None:
    history = RhythmHistory.of([_declared(FOUR_FIFTHS, SEPTEMBER)])

    assert history.on(date(2026, 9, 2)) == 0.0


def test_a_rhythm_does_not_reach_back_before_it_took_effect() -> None:
    # June is read with what June knew, whatever September says.
    history = RhythmHistory.of([_declared(FOUR_FIFTHS, SEPTEMBER)])

    assert history.pattern_on(WEDNESDAY) == FULL_TIME
    assert history.on(WEDNESDAY) == 1.0


def test_the_last_rhythm_in_force_is_the_one_that_applies() -> None:
    history = RhythmHistory.of(
        [_declared(HALF_TIME, SEPTEMBER), _declared(FOUR_FIFTHS, MARCH)]
    )

    assert history.pattern_on(WEDNESDAY) == FOUR_FIFTHS
    assert history.pattern_on(date(2026, 9, 16)) == HALF_TIME


def test_a_rhythm_takes_effect_on_the_very_day_it_opens() -> None:
    history = RhythmHistory.of([_declared(FOUR_FIFTHS, SEPTEMBER)])

    assert history.pattern_on(SEPTEMBER) == FOUR_FIFTHS


def test_nobody_is_expected_at_the_weekend_whatever_they_declared() -> None:
    history = RhythmHistory.of([_declared(FOUR_FIFTHS, MARCH)])

    assert history.on(SATURDAY) == 0.0


def test_a_day_off_says_nothing_about_the_day_that_follows() -> None:
    # Swapping a Wednesday for a Thursday is the teammate's business: the
    # rhythm holds what the week expects, not what the grid allows.
    history = RhythmHistory.of([_declared(FOUR_FIFTHS, MARCH)])

    assert history.on(WEDNESDAY) == 0.0
    assert history.on(THURSDAY) == 1.0


def test_the_rhythm_in_force_carries_the_day_it_opened_on() -> None:
    # The panel shows since when, so the motif alone would not do.
    history = RhythmHistory.of([_declared(FOUR_FIFTHS, MARCH)])

    held = history.in_force_on(WEDNESDAY)
    assert held is not None
    assert held.effective_from == MARCH


def test_nothing_is_in_force_before_the_first_declaration() -> None:
    history = RhythmHistory.of([_declared(FOUR_FIFTHS, SEPTEMBER)])

    assert history.in_force_on(WEDNESDAY) is None


def test_a_rhythm_opening_later_is_not_the_one_in_force_today() -> None:
    # Declaring for next month must not make a screen say somebody is
    # already at four fifths.
    history = RhythmHistory.of([_declared(FOUR_FIFTHS, SEPTEMBER)])

    assert history.latest is not None
    assert history.in_force_on(date(2026, 8, 31)) is None
