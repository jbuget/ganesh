"""What each person still has free, day by day.

Capacity is not declared anywhere: it is deduced. A working day is worth one,
and what is already booked on it — time already delivered, forecasts entered by
hand, leave declared ahead — is taken out. A projection therefore only ever
fills the room the diary actually leaves.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date

#: Below this, a remainder is nothing but a floating-point residue.
EPSILON = 1e-9

#: What one person owes on one working day.
FULL_DAY = 1.0


@dataclass
class Capacity:
    """The room left in everyone's diary, which a projection eats into."""

    _free: dict[int, dict[date, float]] = field(default_factory=dict)

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
        return cls(
            {
                user_id: {
                    day: max(0.0, FULL_DAY - booked.get(user_id, {}).get(day, 0.0))
                    for day in window
                }
                for user_id in user_ids
            }
        )

    def free_on(self, user_id: int, day: date) -> float:
        """Days this person still has free on this day."""
        return self._free.get(user_id, {}).get(day, 0.0)

    def take(self, user_id: int, day: date, wanted: float) -> float:
        """Books up to `wanted` on this person's day. Returns what was taken.

        The projection places fractions of a day, where an entry only ever
        holds a half or a whole one: it announces a date, it does not fill in
        the grid, and rounding here would drift the date it announces.
        """
        free = self.free_on(user_id, day)
        taken = min(free, max(0.0, wanted))
        if taken <= EPSILON:
            return 0.0
        self._free[user_id][day] = free - taken
        return taken
