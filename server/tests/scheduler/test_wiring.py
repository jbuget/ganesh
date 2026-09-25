"""What the clock refuses to start on, and says so rather than falling over."""

from src.core.config import Settings
from src.scheduler.wiring import build_clock


def settings(**overrides: object) -> Settings:
    fields: dict[str, object] = {
        "smtp_host": "smtp.example.test",
        "reminder_send_at": "08:30",
    }
    fields.update(overrides)
    return Settings(**fields)  # type: ignore[arg-type]


def test_no_mail_server_means_no_clock() -> None:
    # The ordinary case on a laptop, and not a failure: the application runs
    # whole and no claim is written every morning for a round going nowhere.
    assert build_clock(settings(smtp_host="")) is None


def test_a_send_time_that_is_not_one_stops_the_clock_and_not_the_api() -> None:
    # A typo in one setting must not stop everybody signing in.
    assert build_clock(settings(reminder_send_at="huit heures et demie")) is None


def test_a_configured_mailer_and_a_real_time_give_a_clock() -> None:
    assert build_clock(settings()) is not None
