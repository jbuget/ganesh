"""Regle de completude d'une journee : la somme ne doit pas depasser 1."""

import pytest

from src.modules.entries.domain.services.day_total import (
    exceeds_one_day,
    remaining_capacity,
)


@pytest.mark.parametrize(
    ("values", "expected"),
    [([], False), ([0.5], False), ([0.5, 0.5], False), ([1.0], False)],
)
def test_a_day_of_at_most_one_is_valid(values: list[float], expected: bool) -> None:
    assert exceeds_one_day(values) is expected


@pytest.mark.parametrize("values", [[1.0, 0.5], [0.5, 0.5, 0.5], [1.0, 1.0]])
def test_a_day_above_one_is_flagged(values: list[float]) -> None:
    assert exceeds_one_day(values) is True


def test_remaining_capacity_of_an_empty_day_is_one() -> None:
    assert remaining_capacity([]) == 1.0


def test_remaining_capacity_after_a_half_day_is_a_half_day() -> None:
    assert remaining_capacity([0.5]) == 0.5


def test_remaining_capacity_never_goes_below_zero() -> None:
    assert remaining_capacity([1.0, 0.5]) == 0.0
