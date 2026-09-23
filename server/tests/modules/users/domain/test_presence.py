"""The week somebody says they work, and from where."""

from datetime import date

import pytest

from src.modules.users.domain.entities.presence import DayPresence, WeekPresence
from src.shared.exceptions.domain_exceptions import ValidationError

MONDAY = date(2026, 9, 21)
WEDNESDAY = date(2026, 9, 23)
SATURDAY = date(2026, 9, 26)


def test_a_week_says_where_one_is_each_day() -> None:
    week = WeekPresence(wednesday=DayPresence.REMOTE, friday=DayPresence.AWAY)

    assert week.on(MONDAY) is DayPresence.ON_SITE
    assert week.on(WEDNESDAY) is DayPresence.REMOTE


def test_nobody_is_anywhere_at_the_weekend() -> None:
    # The week stops on Friday, as the entry grid does: that nobody works at
    # the weekend is an invariant of the domain, not something one declares.
    assert WeekPresence().on(SATURDAY) is DayPresence.AWAY


def test_a_day_holds_one_of_three_things_and_nothing_else() -> None:
    with pytest.raises(ValidationError):
        WeekPresence(monday="au bureau")  # type: ignore[arg-type]


def test_the_days_on_site_are_counted_for_the_team_view() -> None:
    # The figure the screen is opened for: how many are in the office that day.
    week = WeekPresence(
        wednesday=DayPresence.REMOTE,
        thursday=DayPresence.REMOTE,
        friday=DayPresence.AWAY,
    )

    assert week.days_on_site == 2
    assert week.days_present == 4


def test_a_week_nobody_declared_is_not_a_week_of_absences() -> None:
    # Told apart on purpose: « away all week » is something somebody said,
    # « nothing declared » is something nobody has said yet, and a screen that
    # drew them alike would report an empty office that is merely unknown.
    assert WeekPresence.NOT_DECLARED is None
