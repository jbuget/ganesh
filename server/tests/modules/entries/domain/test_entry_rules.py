"""An entry cannot be set on a non-working day."""

from datetime import date

import pytest

from src.modules.entries.domain.services.entry_rules import ensure_day_is_workable
from src.shared.exceptions.domain_exceptions import ValidationError


@pytest.mark.parametrize(
    "day",
    [date(2026, 9, 12), date(2026, 9, 13)],
    ids=["saturday", "sunday"],
)
def test_a_weekend_day_is_refused(day: date) -> None:
    with pytest.raises(ValidationError):
        ensure_day_is_workable(day)


@pytest.mark.parametrize(
    "day",
    [date(2026, 5, 1), date(2026, 12, 25), date(2026, 7, 14)],
    ids=["labour day", "christmas", "bastille day"],
)
def test_a_public_holiday_is_refused(day: date) -> None:
    with pytest.raises(ValidationError):
        ensure_day_is_workable(day)


@pytest.mark.parametrize(
    "day",
    [date(2026, 9, 15), date(2026, 9, 16), date(2026, 9, 18)],
    ids=["tuesday", "wednesday", "friday"],
)
def test_a_working_day_is_accepted(day: date) -> None:
    ensure_day_is_workable(day)


def test_the_error_names_the_day() -> None:
    with pytest.raises(ValidationError, match="2026-09-12"):
        ensure_day_is_workable(date(2026, 9, 12))
