"""What an ordinary week expects of one person."""

from datetime import date

import pytest

from src.modules.calendar.domain.entities.week_pattern import FULL_TIME, WeekPattern
from src.shared.exceptions.domain_exceptions import ValidationError

# The week of Monday 14 September 2026, which runs to Sunday the 20th.
MONDAY = date(2026, 9, 14)
WEDNESDAY = date(2026, 9, 16)
FRIDAY = date(2026, 9, 18)
SATURDAY = date(2026, 9, 19)
SUNDAY = date(2026, 9, 20)


def test_full_time_expects_a_whole_day_on_every_weekday() -> None:
    assert FULL_TIME.on(MONDAY) == 1.0
    assert FULL_TIME.on(WEDNESDAY) == 1.0
    assert FULL_TIME.on(FRIDAY) == 1.0


def test_nobody_is_expected_at_the_weekend_whatever_their_rhythm() -> None:
    assert FULL_TIME.on(SATURDAY) == 0.0
    assert FULL_TIME.on(SUNDAY) == 0.0


def test_a_day_off_expects_nothing_on_that_day_alone() -> None:
    four_fifths = WeekPattern(wednesday=0.0)

    assert four_fifths.on(WEDNESDAY) == 0.0
    assert four_fifths.on(MONDAY) == 1.0


def test_a_half_day_is_a_rhythm_like_any_other() -> None:
    four_and_a_half = WeekPattern(wednesday=0.5)

    assert four_and_a_half.on(WEDNESDAY) == 0.5


def test_a_week_counts_what_it_expects() -> None:
    assert FULL_TIME.days_per_week == 5.0
    assert WeekPattern(wednesday=0.0).days_per_week == 4.0
    assert WeekPattern(wednesday=0.5).days_per_week == 4.5


def test_a_day_is_worth_a_half_or_a_whole_one_or_nothing_at_all() -> None:
    with pytest.raises(ValidationError):
        WeekPattern(monday=0.8)


def test_a_rhythm_expecting_nothing_is_refused() -> None:
    # Expecting nothing of somebody is what deactivating their account says.
    # Said as a rhythm, it would leave a coverage of nought over nought.
    with pytest.raises(ValidationError):
        WeekPattern(monday=0.0, tuesday=0.0, wednesday=0.0, thursday=0.0, friday=0.0)
