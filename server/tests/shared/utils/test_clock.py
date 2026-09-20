"""The clock the application reads, whatever clock the host is set to."""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from src.shared.utils.clock import PARIS, as_instant, now, today


def test_now_returns_an_instant_that_says_which_zone_it_is_in() -> None:
    instant = now()

    assert instant.tzinfo is not None
    assert instant.utcoffset() == datetime.now(UTC).utcoffset()


def test_today_is_the_day_it_is_in_paris_not_on_the_host() -> None:
    assert today() == datetime.now(PARIS).date()


def test_paris_is_the_zone_the_team_lives_in() -> None:
    assert ZoneInfo("Europe/Paris") == PARIS


def test_today_names_tomorrow_when_paris_has_already_turned_the_page() -> None:
    # Half past midnight in Paris is still the evening before in UTC: a
    # declaration entered then belongs to the day the person entering it lives.
    midnight_thirty_in_paris = datetime(2026, 7, 21, 0, 30, tzinfo=PARIS)

    assert midnight_thirty_in_paris.astimezone(UTC).date() == date(2026, 7, 20)
    assert midnight_thirty_in_paris.date() == date(2026, 7, 21)


def test_an_instant_already_carrying_its_zone_is_left_alone() -> None:
    stated = datetime(2026, 7, 20, 8, 30, tzinfo=UTC)

    assert as_instant(stated) == stated


def test_an_instant_given_without_a_zone_is_read_in_paris() -> None:
    assert as_instant(datetime(2026, 7, 20, 10, 30)) == datetime(
        2026, 7, 20, 8, 30, tzinfo=UTC
    )


def test_the_winter_offset_is_followed_without_being_told() -> None:
    assert as_instant(datetime(2026, 1, 20, 10, 30)) == datetime(
        2026, 1, 20, 9, 30, tzinfo=UTC
    )
