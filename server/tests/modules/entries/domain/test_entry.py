"""Invariants of time entry."""

from datetime import date

import pytest

from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.projects.domain.entities.project import ProjectStatus
from src.shared.exceptions.domain_exceptions import ValidationError


def make_entry(value: float = 1.0, day: date = date(2026, 9, 15)) -> Entry:
    return Entry(
        id=None,
        user_id=1,
        project_id=2,
        activity_id=None,
        day=day,
        value=DayValue(value),
        status_at_entry=ProjectStatus.DEVELOPMENT,
    )


@pytest.mark.parametrize("value", [0.25, 0.5, 0.75, 1.0])
def test_a_quarter_of_a_day_and_its_multiples_are_accepted(value: float) -> None:
    """Two hours at a time, on an eight-hour day.

    Somebody carrying half a dozen projects cannot cut a day into halves and
    have it come out right; the quarter is the grain that makes it work.
    """
    assert make_entry(value).value == value


@pytest.mark.parametrize("value", [0.0, 0.125, 0.3, 0.8, 1.25, 1.5, 2.0, -0.25])
def test_any_other_value_is_rejected(value: float) -> None:
    with pytest.raises(ValidationError):
        make_entry(value)


def test_an_entry_remembers_the_project_phase_at_write_time() -> None:
    entry = make_entry()

    assert entry.status_at_entry is ProjectStatus.DEVELOPMENT


def test_an_entry_on_a_future_day_is_a_forecast() -> None:
    entry = make_entry(day=date(2026, 12, 25))

    assert entry.is_forecast(today=date(2026, 9, 15)) is True


def test_an_entry_on_a_past_day_is_actual_time() -> None:
    entry = make_entry(day=date(2026, 8, 3))

    assert entry.is_forecast(today=date(2026, 9, 15)) is False


def test_an_entry_on_today_is_actual_time() -> None:
    """Today counts as delivered: it must not be left out of Monday."""
    entry = make_entry(day=date(2026, 9, 15))

    assert entry.is_forecast(today=date(2026, 9, 15)) is False
