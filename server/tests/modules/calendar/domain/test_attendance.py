"""What somebody said of their own days, and what is supposed beyond them.

The questions this spike exists to answer:

- what a day nobody entered is worth, before the entries and after them;
- whether a habit read off the last weeks is enough to plan on, months ahead
  of anything anybody has entered;
- whether entering a month is cheap enough that people will actually do it.
"""

from datetime import date, timedelta

from src.modules.calendar.domain.entities.attendance import Attendance, habit_of
from src.modules.calendar.domain.entities.week_pattern import FULL_TIME, WeekPattern

# Four full weeks, Monday 31 August to Friday 25 September 2026. No holiday.
WEEKS = [
    [date(2026, 8, 31) + timedelta(days=offset + 7 * week) for offset in range(5)]
    for week in range(4)
]
MONDAYS = [week[0] for week in WEEKS]
WEDNESDAYS = [week[2] for week in WEEKS]

LAST_ENTERED = WEEKS[-1][-1]  # Friday 25 September 2026
LATER = date(2026, 12, 7)  # A Monday, well beyond anything entered
EARLIER = date(2026, 5, 4)  # A Monday, well before anything entered

SATURDAY = date(2026, 9, 19)


def four_weeks(**exceptions: float) -> dict[date, float]:
    """Four ordinary weeks, with the days named in `exceptions` overridden.

    Keys read « w0d2 »: week 0, Wednesday. Enough to say « off every
    Wednesday » or « off that one Thursday » without listing twenty days.
    """
    days = {day: 1.0 for week in WEEKS for day in week}
    for key, value in exceptions.items():
        week, weekday = int(key[1]), int(key[3])
        days[WEEKS[week][weekday]] = value
    return days


class TestWhatADayIsWorth:
    def test_a_day_entered_is_worth_what_was_entered(self) -> None:
        attendance = Attendance.of(four_weeks(w0d2=0.0))

        assert attendance.on(WEDNESDAYS[0]) == 0.0
        assert attendance.on(MONDAYS[0]) == 1.0

    def test_nobody_is_expected_at_the_weekend_whatever_was_entered(self) -> None:
        attendance = Attendance.of({**four_weeks(), SATURDAY: 1.0})

        assert attendance.on(SATURDAY) == 0.0

    def test_a_day_before_anything_was_entered_is_read_as_full_time(self) -> None:
        # What the application assumed of everybody before attendance existed:
        # a default that moves no figure already computed is the only honest
        # one. May is not rewritten by what September says.
        attendance = Attendance.of(four_weeks(w0d2=0.0, w1d2=0.0, w2d2=0.0, w3d2=0.0))

        assert attendance.on(EARLIER) == 1.0


class TestWhatIsSupposedBeyondTheEntries:
    """The hard question: Planification reads 12 months, entry covers one."""

    def test_beyond_the_entries_the_habit_of_the_last_weeks_holds(self) -> None:
        # Four Wednesdays off in a row is not an accident, and a plan that
        # gave this person back their Wednesdays in December would promise
        # days nobody is going to work.
        attendance = Attendance.of(four_weeks(w0d2=0.0, w1d2=0.0, w2d2=0.0, w3d2=0.0))

        assert attendance.on(date(2026, 12, 9)) == 0.0  # a Wednesday
        assert attendance.on(LATER) == 1.0  # a Monday

    def test_a_single_day_off_does_not_become_a_habit(self) -> None:
        # One Thursday taken off out of four is a day off, not a rhythm.
        attendance = Attendance.of(four_weeks(w2d3=0.0))

        assert attendance.on(date(2026, 12, 10)) == 1.0  # a Thursday

    def test_with_nothing_entered_at_all_everyone_is_read_as_full_time(self) -> None:
        attendance = Attendance.of({})

        assert attendance.on(LATER) == 1.0
        assert attendance.habit == FULL_TIME

    def test_the_habit_is_told_apart_from_what_was_entered(self) -> None:
        # A screen must be able to draw the two differently: a fact and a
        # supposition are never drawn alike.
        attendance = Attendance.of(four_weeks(w0d2=0.0, w1d2=0.0, w2d2=0.0, w3d2=0.0))

        assert attendance.was_entered(WEDNESDAYS[0]) is True
        assert attendance.was_entered(LATER) is False


class TestTheHabitRead:
    def test_a_day_off_every_week_becomes_the_habit(self) -> None:
        habit = habit_of(four_weeks(w0d2=0.0, w1d2=0.0, w2d2=0.0, w3d2=0.0))

        assert habit == WeekPattern(wednesday=0.0)
        assert habit.days_per_week == 4.0

    def test_a_half_day_every_week_becomes_the_habit(self) -> None:
        habit = habit_of(four_weeks(w0d2=0.5, w1d2=0.5, w2d2=0.5, w3d2=0.5))

        assert habit == WeekPattern(wednesday=0.5)

    def test_the_habit_follows_the_majority_of_the_weeks_read(self) -> None:
        # Three weeks out of four without a Wednesday: the odd one back does
        # not undo the habit.
        habit = habit_of(four_weeks(w0d2=0.0, w1d2=0.0, w2d2=0.0))

        assert habit.wednesday == 0.0

    def test_a_tie_follows_the_most_recent_weeks(self) -> None:
        # Two and two: somebody is changing their days, and the change is
        # what the weeks to come will look like.
        habit = habit_of(four_weeks(w0d2=0.0, w1d2=0.0))

        assert habit.wednesday == 1.0

    def test_only_the_last_weeks_are_read(self) -> None:
        # A rhythm left behind in the spring says nothing about the autumn.
        spring = {date(2026, 5, 4) + timedelta(days=n): 0.0 for n in range(5)}
        habit = habit_of({**spring, **four_weeks()})

        assert habit == FULL_TIME
