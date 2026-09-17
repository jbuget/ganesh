"""Une saisie ne peut pas etre posee sur un jour non ouvre."""

from datetime import date

import pytest

from src.modules.entries.domain.services.entry_rules import ensure_day_is_workable
from src.shared.exceptions.domain_exceptions import ValidationError


@pytest.mark.parametrize(
    "jour",
    [date(2026, 9, 12), date(2026, 9, 13)],
    ids=["samedi", "dimanche"],
)
def test_a_weekend_day_is_refused(jour: date) -> None:
    with pytest.raises(ValidationError):
        ensure_day_is_workable(jour)


@pytest.mark.parametrize(
    "jour",
    [date(2026, 5, 1), date(2026, 12, 25), date(2026, 7, 14)],
    ids=["1er mai", "noel", "14 juillet"],
)
def test_a_public_holiday_is_refused(jour: date) -> None:
    with pytest.raises(ValidationError):
        ensure_day_is_workable(jour)


@pytest.mark.parametrize(
    "jour",
    [date(2026, 9, 15), date(2026, 9, 16), date(2026, 9, 18)],
    ids=["mardi", "mercredi", "vendredi"],
)
def test_a_working_day_is_accepted(jour: date) -> None:
    ensure_day_is_workable(jour)


def test_the_error_names_the_day() -> None:
    with pytest.raises(ValidationError, match="2026-09-12"):
        ensure_day_is_workable(date(2026, 9, 12))
