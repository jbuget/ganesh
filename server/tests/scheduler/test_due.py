"""What the clock decides is owed, and when it decides nothing is."""

from datetime import datetime, time
from zoneinfo import ZoneInfo

from src.modules.users.domain.entities.reminder_cadence import ReminderCadence
from src.scheduler.due import cadences_due, first_working_day_of_week
from src.shared.utils.clock import PARIS

UTC = ZoneInfo("UTC")
AT = time(8, 30)


def paris(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=PARIS)


class TestNothingBeforeTheHour:
    def test_nothing_is_owed_before_the_send_time(self) -> None:
        assert cadences_due(paris(2026, 9, 23, 7, 0), AT) == []

    def test_the_daily_round_is_owed_once_the_hour_has_passed(self) -> None:
        assert cadences_due(paris(2026, 9, 23, 8, 30), AT) == [ReminderCadence.DAILY]


class TestNothingOnADayNobodyWorks:
    def test_a_saturday_owes_nothing(self) -> None:
        assert cadences_due(paris(2026, 9, 26, 9, 0), AT) == []

    def test_a_public_holiday_owes_nothing(self) -> None:
        # 15 August. A letter that day is noise, and noise is what makes
        # somebody filter the one that mattered.
        assert cadences_due(paris(2026, 8, 15, 9, 0), AT) == []


class TestTheWeeklyRound:
    def test_it_goes_out_on_the_first_working_day_of_the_week(self) -> None:
        # Monday 21 September 2026.
        assert ReminderCadence.WEEKLY in cadences_due(paris(2026, 9, 21, 9, 0), AT)

    def test_it_does_not_go_out_again_on_the_tuesday(self) -> None:
        assert cadences_due(paris(2026, 9, 22, 9, 0), AT) == [ReminderCadence.DAILY]

    def test_a_week_opening_on_a_holiday_sends_on_the_next_working_day(self) -> None:
        # 1 May 2028 falls on a Monday: the week opens on the Tuesday.
        assert first_working_day_of_week(paris(2028, 5, 3, 9, 0).date()).day == 2


class TestTheClockIsReadInParis:
    def test_an_instant_in_utc_is_read_as_the_local_hour(self) -> None:
        # 06:45 UTC is 08:45 in Paris in September: the round is owed.
        instant = datetime(2026, 9, 23, 6, 45, tzinfo=UTC)

        assert cadences_due(instant, AT) == [ReminderCadence.DAILY]

    def test_the_same_clock_hour_in_winter_is_not_yet_the_hour(self) -> None:
        # 06:45 UTC is 07:45 in Paris in January: too early.
        instant = datetime(2026, 1, 21, 6, 45, tzinfo=UTC)

        assert cadences_due(instant, AT) == []
