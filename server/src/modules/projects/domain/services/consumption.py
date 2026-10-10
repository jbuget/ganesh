"""What each trade of a mission has cost, against what it was budgeted at.

A mission reads the sum of what its trades are budgeted at, and each trade
carries the budget for its own: the comparison that steers is made trade by
trade, because a ratio drawn on the whole mission lets a build budget absorb
the days of a design nobody planned.

Delivered is told from forecast, as everywhere else: an entry on a day after
today is a supposition, and it must not eat into what a trade has left.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from src.modules.projects.domain.entities.activity import Activity


@dataclass(frozen=True)
class TradeConsumption:
    """One trade, and the days booked under it.

    `activity` is `None` for the days booked under no trade at all — what the
    reprise took over, where nobody ever said which trade the days were spent
    under, and filling one in would invent it.
    """

    activity: Activity | None
    delivered: float
    forecast: float

    @property
    def budget(self) -> float | None:
        return None if self.activity is None else self.activity.estimated_days

    @property
    def left(self) -> float | None:
        """What the budget has left, forecast aside. Nothing to say without one."""
        if self.budget is None:
            return None
        return round(self.budget - self.delivered, 2)


def by_trade(
    activities: list[Activity],
    days: Iterable[tuple[int | None, date, float]],
    today: date,
) -> list[TradeConsumption]:
    """The consumption of every trade, then of the days under none.

    `days` is `(activity id, day, value)`, so that the domain of the projects
    reads no entry. An archived trade is listed only when it carries days: it
    is no longer booked against, and an empty line would be noise.
    """
    delivered: dict[int | None, float] = {}
    forecast: dict[int | None, float] = {}
    for activity_id, day, value in days:
        held = forecast if day > today else delivered
        held[activity_id] = held.get(activity_id, 0.0) + value

    def read(activity: Activity | None) -> TradeConsumption:
        key = None if activity is None else activity.id
        return TradeConsumption(
            activity=activity,
            delivered=round(delivered.get(key, 0.0), 2),
            forecast=round(forecast.get(key, 0.0), 2),
        )

    listed = [
        read(activity)
        for activity in activities
        if activity.is_active or activity.id in delivered or activity.id in forecast
    ]
    if None in delivered or None in forecast:
        listed.append(read(None))
    return listed
