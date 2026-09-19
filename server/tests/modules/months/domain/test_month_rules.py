"""The rules every write on a month goes through."""

from datetime import date

import pytest

from src.modules.months.domain.entities.month import Month
from src.modules.months.domain.services.month_period import first_day_of
from src.modules.months.domain.services.month_rules import ensure_month_is_open
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import ForbiddenActionError

ALICE = User(
    id=1,
    entra_oid="oid-1",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)


def test_a_month_is_held_by_its_first_day() -> None:
    assert first_day_of(date(2026, 9, 24)) == date(2026, 9, 1)


def test_the_first_day_of_a_month_is_left_as_it_is() -> None:
    assert first_day_of(date(2026, 9, 1)) == date(2026, 9, 1)


def test_a_month_nobody_ever_touched_accepts_a_write() -> None:
    """No record means no validation: the month is open."""
    ensure_month_is_open(None)


def test_an_open_month_accepts_a_write() -> None:
    ensure_month_is_open(Month(user_id=1, month=date(2026, 9, 1)))


def test_a_validated_month_refuses_a_write() -> None:
    month = Month(user_id=1, month=date(2026, 9, 1))
    month.validate(by=ALICE)

    with pytest.raises(ForbiddenActionError):
        ensure_month_is_open(month)


def test_a_month_reopened_accepts_a_write_again() -> None:
    month = Month(user_id=1, month=date(2026, 9, 1))
    month.validate(by=ALICE)
    month.reopen(by=User(**{**ALICE.__dict__, "role": Role.MANAGER}))

    ensure_month_is_open(month)
