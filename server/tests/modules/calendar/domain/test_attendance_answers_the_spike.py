"""The three questions the spike was opened to answer, answered by example.

1. Does an expectation read over a window still work, across entered days,
   days before any entry, and days beyond them?
2. Can Planification plan twelve months ahead on one month of entries?
3. Is entering a month cheap enough that anybody will keep doing it?
"""

from datetime import date, timedelta

from src.modules.calendar.domain.entities.attendance import Attendance
from src.modules.calendar.domain.entities.period import Period
from src.modules.calendar.domain.services.working_days import working_days_between

TODAY = date(2026, 9, 23)


def entered_from(opens_on: date, weeks: int, **off: float) -> dict[date, float]:
    """`weeks` weeks of working days from a Monday, some weekdays overridden."""
    days: dict[date, float] = {}
    for week in range(weeks):
        for weekday in range(5):
            day = opens_on + timedelta(days=weekday + 7 * week)
            days[day] = off.get(("mon", "tue", "wed", "thu", "fri")[weekday], 1.0)
    return days


def expected_over(period: Period, attendance: Attendance) -> float:
    """What the window calls for from this person — how a screen would ask."""
    return round(
        sum(
            attendance.on(day) for day in working_days_between(period.start, period.end)
        ),
        2,
    )


class TestAWindowReadAcrossTheThreeZones:
    def test_a_month_entered_is_counted_as_entered(self) -> None:
        # September 2026 holds 22 working days, 5 of them Wednesdays.
        attendance = Attendance.of(entered_from(date(2026, 8, 31), 5, wed=0.0))

        september = Period(start=date(2026, 9, 1), end=date(2026, 9, 30))
        assert expected_over(september, attendance) == 17

    def test_a_month_before_any_entry_is_counted_full_time(self) -> None:
        # June is not rewritten by what September says: the figures already
        # read over the spring stay as they were read.
        attendance = Attendance.of(entered_from(date(2026, 8, 31), 4, wed=0.0))

        june = Period(start=date(2026, 6, 1), end=date(2026, 6, 30))
        assert expected_over(june, attendance) == 22

    def test_a_month_beyond_the_entries_is_counted_on_the_habit(self) -> None:
        # December holds 23 working days, 5 of them Wednesdays, and the 25th
        # is a holiday the calendar already takes out.
        attendance = Attendance.of(entered_from(date(2026, 8, 31), 4, wed=0.0))

        december = Period(start=date(2026, 12, 1), end=date(2026, 12, 31))
        full_time = Attendance.of({})

        assert expected_over(december, full_time) == 22
        assert expected_over(december, attendance) == 17


class TestPlanningTwelveMonthsOnOneMonthOfEntries:
    def test_the_habit_carries_the_whole_horizon(self) -> None:
        # The question that decides the design: entry covers a month, the plan
        # reads a year. Read off the last weeks, the habit covers the rest —
        # and a part-timer is never given back days they do not work.
        attendance = Attendance.of(entered_from(date(2026, 8, 31), 4, wed=0.0))

        horizon = Period(start=TODAY, end=date(2027, 9, 22))
        working = len(working_days_between(horizon.start, horizon.end))
        supposed = expected_over(horizon, attendance)

        # Four fifths of a year, give or take the holidays that fall on the
        # days they work.
        assert 0.78 <= supposed / working <= 0.82

    def test_nothing_entered_plans_exactly_as_the_application_does_today(self) -> None:
        # The default has to move no plan: it is what was assumed of everybody
        # before attendance existed.
        horizon = Period(start=TODAY, end=date(2027, 9, 22))

        assert expected_over(horizon, Attendance.of({})) == len(
            working_days_between(horizon.start, horizon.end)
        )

    def test_a_habit_is_read_even_from_entries_that_stopped_long_ago(self) -> None:
        # Somebody who entered in March and never came back still plans as the
        # March weeks said — better than as a full-timer they are not.
        attendance = Attendance.of(entered_from(date(2026, 3, 2), 4, wed=0.0, fri=0.0))

        assert attendance.habit.days_per_week == 3.0
        assert attendance.on(date(2026, 12, 9)) == 0.0


class TestWhatEnteringAMonthCosts:
    """A screen nobody fills in is worth nothing, however right its model."""

    @staticmethod
    def gestures(month: Period, attendance: Attendance) -> int:
        """Days of the month that differ from what the habit would fill in.

        The number of cells somebody has to touch if the screen opens
        pre-filled on their habit — which is the only way this is worth
        opening every month.
        """
        return sum(
            1
            for day in working_days_between(month.start, month.end)
            if attendance.on(day) != attendance.habit.on(day)
        )

    def test_an_unchanging_month_costs_nothing_at_all(self) -> None:
        # Four fifths, every week, for good: the month opens already right.
        habit = entered_from(date(2026, 8, 31), 4, wed=0.0)
        october = entered_from(date(2026, 9, 28), 4, wed=0.0)
        attendance = Attendance.of({**habit, **october})

        assert (
            self.gestures(Period(date(2026, 10, 1), date(2026, 10, 30)), attendance)
            == 0
        )

    def test_a_week_of_leave_costs_its_own_days_and_no_more(self) -> None:
        habit = entered_from(date(2026, 8, 31), 4)
        october = entered_from(date(2026, 9, 28), 4)
        for day in range(5):
            october[date(2026, 10, 12) + timedelta(days=day)] = 0.0
        attendance = Attendance.of({**habit, **october})

        assert (
            self.gestures(Period(date(2026, 10, 1), date(2026, 10, 30)), attendance)
            == 5
        )

    def test_swapping_a_wednesday_for_a_thursday_costs_two(self) -> None:
        # The case a motif could never say, and this says exactly.
        habit = entered_from(date(2026, 8, 31), 4, wed=0.0)
        october = entered_from(date(2026, 9, 28), 4, wed=0.0)
        october[date(2026, 10, 14)] = 1.0  # a Wednesday worked
        october[date(2026, 10, 15)] = 0.0  # the Thursday given back
        attendance = Attendance.of({**habit, **october})

        assert (
            self.gestures(Period(date(2026, 10, 1), date(2026, 10, 30)), attendance)
            == 2
        )

    def test_the_habit_still_holds_when_the_month_is_full_of_exceptions(self) -> None:
        # A month off does not become the habit: the four weeks read are the
        # ones entered last, and a return re-reads them.
        habit = entered_from(date(2026, 8, 31), 4, wed=0.0)
        attendance = Attendance.of(habit)

        assert attendance.habit.days_per_week == 4.0


class TestWhatTheModelDoesNotDo:
    def test_a_habit_read_off_an_absence_supposes_the_absence_goes_on(self) -> None:
        # Worth knowing rather than hiding: somebody who entered a month of
        # leave and nothing after plans as absent for good. A screen must say
        # so — « supposé d'après vos dernières semaines » — and the entry of
        # the following weeks is what puts it right.
        away = {day: 0.0 for day in entered_from(date(2026, 8, 31), 4)}
        attendance = Attendance.of(away)

        assert attendance.habit.days_per_week == 0.0
        assert attendance.on(date(2026, 12, 9)) == 0.0
        assert attendance.was_entered(date(2026, 12, 9)) is False
