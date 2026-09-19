"""What each person still has free, day by day.

Capacity is not declared anywhere: it is deduced. A working day is worth one,
and what is already booked on it — time already delivered, forecasts entered by
hand, leave declared ahead — is taken out. A projection therefore only ever
fills the room the diary actually leaves.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, timedelta

#: Below this, a remainder is nothing but a floating-point residue.
EPSILON = 1e-9

#: What one person owes on one working day.
FULL_DAY = 1.0

#: Half a day a week nobody may plan on.
#:
#: Meetings happen, and so do the absences nobody saw coming. A plan that
#: booked every last half day would be wrong every week, and a plan that is
#: always wrong steers nothing. The half day is held back from what the
#: projection may place; it is not time off, and what somebody actually
#: declares on it is their business.
WEEKLY_RESERVE_DAYS = 0.5


def week_of(day: date) -> date:
    """The Monday of the week a day belongs to."""
    return day - timedelta(days=day.weekday())


def weekly_allowance(capacity: float, booked: float) -> float:
    """What a projection may place on one person during one week.

    The week's working days, less the half day held back, less whatever is
    already declared on it. Never negative: a week someone has already filled
    past the reserve offers nothing, it does not borrow from the next one.

    A week the window only sees part of — the one a horizon opens in the
    middle of — still holds its half day back. Slightly cautious on that first
    week, and never optimistic anywhere, which is the way round a plan should
    be wrong.
    """
    return max(0.0, capacity - WEEKLY_RESERVE_DAYS - booked)


@dataclass
class Capacity:
    """The room left in everyone's diary, which a projection eats into.

    Two limits, not one. A day never holds more than a day, and a week never
    holds more than its allowance: without the first, somebody would work two
    projects on one Tuesday; without the second, the half day kept for what
    nobody saw coming would be planned away like any other.
    """

    _free: dict[int, dict[date, float]] = field(default_factory=dict)
    #: What each person may still be given during each week.
    _weekly: dict[int, dict[date, float]] = field(default_factory=dict)

    @classmethod
    def over(
        cls,
        user_ids: Iterable[int],
        days: Iterable[date],
        booked: Mapping[int, Mapping[date, float]],
    ) -> "Capacity":
        """Room left for these people over these days, given what is booked.

        A day booked beyond a full day leaves no room rather than a negative
        one: over-booking is a warning the grid already carries, and it must
        not lend capacity to the projection.
        """
        window = list(days)

        capacity_by_week: dict[date, float] = {}
        for day in window:
            week = week_of(day)
            capacity_by_week[week] = capacity_by_week.get(week, 0.0) + FULL_DAY

        free: dict[int, dict[date, float]] = {}
        weekly: dict[int, dict[date, float]] = {}
        for user_id in user_ids:
            diary = booked.get(user_id, {})

            free[user_id] = {
                day: max(0.0, FULL_DAY - diary.get(day, 0.0)) for day in window
            }

            booked_by_week: dict[date, float] = {}
            for day in window:
                week = week_of(day)
                booked_by_week[week] = booked_by_week.get(week, 0.0) + diary.get(
                    day, 0.0
                )

            weekly[user_id] = {
                week: weekly_allowance(capacity, booked_by_week.get(week, 0.0))
                for week, capacity in capacity_by_week.items()
            }

        return cls(free, weekly)

    def free_on(self, user_id: int, day: date) -> float:
        """Days this person may still be given on this day.

        The lesser of what the day has left and what the week still allows:
        a Friday is free, but not if the week is already spent.
        """
        return min(
            self._free.get(user_id, {}).get(day, 0.0),
            self._weekly.get(user_id, {}).get(week_of(day), 0.0),
        )

    def take(self, user_id: int, day: date, wanted: float) -> float:
        """Books up to `wanted` on this person's day. Returns what was taken.

        The projection places fractions of a day, where an entry only ever
        holds a half or a whole one: it announces a date, it does not fill in
        the grid, and rounding here would drift the date it announces.
        """
        taken = min(self.free_on(user_id, day), max(0.0, wanted))
        if taken <= EPSILON:
            return 0.0

        week = week_of(day)
        self._free[user_id][day] -= taken
        self._weekly[user_id][week] -= taken
        return taken
