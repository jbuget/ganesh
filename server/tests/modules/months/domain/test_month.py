"""Cycle de vie d'un mois : ouvert, valide, rouvert."""

from datetime import date

import pytest

from src.modules.months.domain.entities.month import Month, MonthState
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import ForbiddenActionError


def make_user(role: Role) -> User:
    return User(
        id=1 if role is Role.TEAMMATE else 2,
        entra_oid="oid",
        email="x@waat.fr",
        display_name="X",
        role=role,
    )


def make_month(state: MonthState = MonthState.OPEN) -> Month:
    month = Month(user_id=1, month=date(2026, 9, 1))
    if state is MonthState.VALIDATED:
        month.validate(by=make_user(Role.TEAMMATE))
    return month


def test_a_month_starts_open() -> None:
    assert make_month().state is MonthState.OPEN


def test_an_open_month_accepts_writes() -> None:
    assert make_month().is_writable is True


def test_a_validated_month_is_immutable() -> None:
    assert make_month(MonthState.VALIDATED).is_writable is False


def test_a_user_validates_their_own_month() -> None:
    month = Month(user_id=1, month=date(2026, 9, 1))

    month.validate(by=make_user(Role.TEAMMATE))

    assert month.state is MonthState.VALIDATED
    assert month.validated_by == 1


def test_validating_an_already_validated_month_is_rejected() -> None:
    month = make_month(MonthState.VALIDATED)

    with pytest.raises(ForbiddenActionError):
        month.validate(by=make_user(Role.TEAMMATE))


def test_a_teammate_cannot_reopen_a_validated_month() -> None:
    month = make_month(MonthState.VALIDATED)

    with pytest.raises(ForbiddenActionError):
        month.reopen(by=make_user(Role.TEAMMATE))


def test_a_manager_can_reopen_a_validated_month() -> None:
    month = make_month(MonthState.VALIDATED)

    month.reopen(by=make_user(Role.MANAGER))

    assert month.state is MonthState.OPEN
    assert month.is_writable is True


def test_reopening_keeps_track_of_who_did_it() -> None:
    month = make_month(MonthState.VALIDATED)

    month.reopen(by=make_user(Role.MANAGER))

    assert month.reopened_by == 2


def test_reopening_an_open_month_is_rejected() -> None:
    with pytest.raises(ForbiddenActionError):
        make_month().reopen(by=make_user(Role.MANAGER))


def test_the_month_is_normalised_to_its_first_day() -> None:
    month = Month(user_id=1, month=date(2026, 9, 23))

    assert month.month == date(2026, 9, 1)
