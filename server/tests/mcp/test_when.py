"""Reading a month a model wrote: « 2026-09 », or nothing at all."""

from datetime import date

from src.mcp.tools.when import month_asked


def test_a_month_is_read_as_its_first_day() -> None:
    assert month_asked("2026-09") == date(2026, 9, 1)


def test_surrounding_spaces_are_forgiven() -> None:
    assert month_asked(" 2026-09 ") == date(2026, 9, 1)


def test_nothing_asked_is_the_month_running(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr("src.mcp.tools.when.clock.today", lambda: date(2026, 10, 11))

    assert month_asked(None) == date(2026, 10, 1)


def test_a_month_that_does_not_exist_is_not_read() -> None:
    assert month_asked("2026-13") is None


def test_something_that_is_not_a_month_is_not_read() -> None:
    assert month_asked("septembre") is None
    assert month_asked("2026-09-21") is None
