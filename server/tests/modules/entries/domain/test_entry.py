"""Invariants de la saisie de temps."""

from datetime import date

import pytest

from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.projects.domain.entities.project import ProjectStatus
from src.shared.exceptions.domain_exceptions import ValidationError


def make_entry(valeur: float = 1.0, jour: date = date(2026, 9, 15)) -> Entry:
    return Entry(
        id=None,
        user_id=1,
        project_id=2,
        jour=jour,
        valeur=DayValue(valeur),
        statut_at_entry=ProjectStatus.REALISATION,
    )


@pytest.mark.parametrize("valeur", [0.5, 1.0])
def test_a_half_day_or_a_full_day_is_accepted(valeur: float) -> None:
    assert make_entry(valeur).valeur == valeur


@pytest.mark.parametrize("valeur", [0.0, 0.25, 0.75, 1.5, 2.0, -0.5])
def test_any_other_value_is_rejected(valeur: float) -> None:
    with pytest.raises(ValidationError):
        make_entry(valeur)


def test_an_entry_remembers_the_project_phase_at_write_time() -> None:
    entry = make_entry()

    assert entry.statut_at_entry is ProjectStatus.REALISATION


def test_an_entry_on_a_future_day_is_a_forecast() -> None:
    entry = make_entry(jour=date(2026, 12, 25))

    assert entry.is_forecast(today=date(2026, 9, 15)) is True


def test_an_entry_on_a_past_day_is_actual_time() -> None:
    entry = make_entry(jour=date(2026, 8, 3))

    assert entry.is_forecast(today=date(2026, 9, 15)) is False


def test_an_entry_on_today_is_actual_time() -> None:
    """Le jour courant compte comme realise : il ne doit pas etre exclu de Monday."""
    entry = make_entry(jour=date(2026, 9, 15))

    assert entry.is_forecast(today=date(2026, 9, 15)) is False
