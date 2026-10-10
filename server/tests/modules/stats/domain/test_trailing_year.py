"""The year the activity mosaic is drawn over."""

from datetime import date

from src.modules.stats.domain.services.trailing_year import trailing_year


def test_the_year_ends_today() -> None:
    assert trailing_year(date(2026, 10, 10)).end == date(2026, 10, 10)


def test_the_year_holds_three_hundred_and_sixty_five_days() -> None:
    year = trailing_year(date(2026, 10, 10))

    assert year.start == date(2025, 10, 11)
    assert year.length_in_days == 365


def test_a_year_holding_a_29th_of_february_holds_three_hundred_and_sixty_six() -> None:
    year = trailing_year(date(2024, 10, 10))

    assert year.start == date(2023, 10, 11)
    assert year.length_in_days == 366


def test_the_29th_of_february_is_read_as_the_day_after_the_28th_of_last_year() -> None:
    year = trailing_year(date(2024, 2, 29))

    assert year.start == date(2023, 3, 1)
    assert year.length_in_days == 366
