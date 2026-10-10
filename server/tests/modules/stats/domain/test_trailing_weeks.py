"""The weeks the coverage curve is drawn over."""

from datetime import date

from src.modules.stats.domain.services.trailing_weeks import trailing_weeks

# A Thursday.
TODAY = date(2026, 9, 17)


def test_the_weeks_come_oldest_first_each_opening_on_a_monday() -> None:
    weeks = trailing_weeks(TODAY, count=3)

    assert [week.start for week in weeks] == [
        date(2026, 8, 31),
        date(2026, 9, 7),
        date(2026, 9, 14),
    ]
    assert all(week.start.weekday() == 0 for week in weeks)


def test_a_week_already_over_runs_to_its_sunday() -> None:
    assert trailing_weeks(TODAY, count=2)[0].end == date(2026, 9, 13)


def test_the_week_running_stops_today() -> None:
    # What comes after is a forecast, and a forecast is not owed yet.
    assert trailing_weeks(TODAY, count=1)[0].end == TODAY
