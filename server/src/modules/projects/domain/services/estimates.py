"""What a mission is estimated at, now that its activities carry the budget.

A mission cut into activities no longer holds an estimate of its own: each
trade carries the days budgeted for it, and the mission reads their sum. That
is the whole point of the level — an estimate counted in build days stops
being comparable the moment the days of every trade are taken off it.
"""

from collections.abc import Iterable

from src.modules.projects.domain.entities.activity import Activity


def estimate_of(
    activities: Iterable[Activity], own: float | None = None
) -> float | None:
    """The estimate of a mission, read from the trades it is cut into.

    Three answers, and the middle one is the one that matters:

    A mission nobody has cut up yet reads the estimate it carries itself.
    Nothing is lost while the reference list is being cut up trade by trade,
    and a mission that never will be keeps reading as it always did.

    A mission whose every activity is budgeted reads their sum.

    A mission where one activity is budgeted and another is not reads
    **nothing**, rather than the sum of what happens to be filled in. A ratio
    drawn from half the trades would announce an overrun on a mission whose
    budget is simply incomplete, and that figure turns red on a screen
    somebody steers by. Days consumed still read; only the comparison waits
    until the estimate is whole.

    Archived activities are left out: they are no longer booked against, and
    their budget is no longer part of what the mission has left to spend.
    """
    live = [activity for activity in activities if activity.is_active]
    if not live:
        return own

    if any(activity.estimated_days is None for activity in live):
        return None

    return round(sum(activity.estimated_days or 0.0 for activity in live), 2)
