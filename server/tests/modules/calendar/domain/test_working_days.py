"""Jours ouvres, week-ends et jours feries francais."""

from datetime import date

import pytest

from src.modules.calendar.domain.services.working_days import (
    DayKind,
    classify_day,
    days_of_month,
    working_days_count,
)

# Feries 2026 utilises ici : 1er janvier, 6 avril (lundi de Paques),
# 1er mai, 14 juillet, 25 decembre.


@pytest.mark.parametrize("jour", [date(2026, 9, 12), date(2026, 9, 13)])
def test_a_weekend_day_is_flagged_as_weekend(jour: date) -> None:
    assert classify_day(jour) is DayKind.WEEKEND


def test_a_public_holiday_is_flagged_as_holiday() -> None:
    assert classify_day(date(2026, 5, 1)) is DayKind.FERIE


def test_a_regular_weekday_is_a_working_day() -> None:
    assert classify_day(date(2026, 9, 15)) is DayKind.OUVRE


def test_christmas_is_a_holiday() -> None:
    assert classify_day(date(2026, 12, 25)) is DayKind.FERIE


def test_a_holiday_falling_on_a_weekend_is_reported_as_a_holiday() -> None:
    """Le 15 aout 2026 tombe un samedi : la nature feriee prime a l'affichage."""
    assert classify_day(date(2026, 8, 15)) is DayKind.FERIE


def test_a_month_lists_all_its_days() -> None:
    days = days_of_month(2026, 9)

    assert len(days) == 30
    assert days[0].jour == date(2026, 9, 1)
    assert days[-1].jour == date(2026, 9, 30)


def test_february_of_a_leap_year_has_twenty_nine_days() -> None:
    assert len(days_of_month(2028, 2)) == 29


def test_each_day_of_the_month_carries_its_kind() -> None:
    days = {day.jour: day.kind for day in days_of_month(2026, 5)}

    assert days[date(2026, 5, 1)] is DayKind.FERIE
    assert days[date(2026, 5, 2)] is DayKind.WEEKEND
    assert days[date(2026, 5, 4)] is DayKind.OUVRE


def test_working_days_count_excludes_weekends_and_holidays() -> None:
    """Mai 2026 : 31 jours, 10 jours de week-end, 3 feries en semaine."""
    days = days_of_month(2026, 5)
    expected = sum(1 for day in days if day.kind is DayKind.OUVRE)

    assert working_days_count(2026, 5) == expected
    assert working_days_count(2026, 5) < 31
