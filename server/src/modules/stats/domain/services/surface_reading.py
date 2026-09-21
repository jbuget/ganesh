"""Folding what was recorded into what the table reads.

The folding is the rule: two gestures of one person on one function make one
person, and the gestures of four kinds of action make one figure. Doing it in
SQL would scatter the map of the product across a `CASE` nobody reads.
"""

from collections.abc import Mapping
from datetime import date

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.stats.domain.entities.surface_usage import (
    SURFACE_OF,
    Surface,
    SurfaceActivity,
    SurfaceUsage,
    WindowReading,
)


def read_surfaces(
    current: WindowReading,
    previous: WindowReading,
    last_used: Mapping[Surface, date],
) -> SurfaceUsage:
    """Lays every function of the product out, in the order they are declared.

    Every surface gets its line, touched or not: a zero is a reading, and a
    function missing from the table would pass for one that is doing fine.
    """
    people, gestures = _fold(current)
    before, _ = _fold(previous)

    return SurfaceUsage(
        activities=tuple(
            SurfaceActivity(
                surface=surface,
                people=people.get(surface, 0),
                gestures=gestures.get(surface, 0),
                previous_people=before.get(surface, 0),
                last_used_on=last_used.get(surface),
            )
            for surface in Surface
        )
    )


def surfaces_last_used(
    gestures: Mapping[AuditAction, date],
    others: Mapping[Surface, date],
) -> dict[Surface, date]:
    """The day each function was last used, whatever it is read from.

    Several gestures answer for one function, and the latest of them is the
    one that dates it.
    """
    last_used: dict[Surface, date] = dict(others)
    for action, day in gestures.items():
        surface = SURFACE_OF[action]
        known = last_used.get(surface)
        if known is None or day > known:
            last_used[surface] = day
    return last_used


def _fold(reading: WindowReading) -> tuple[dict[Surface, int], dict[Surface, int]]:
    """Gathers a window's traces and tallies per function: who, and how much.

    The actors are held as a set while folding and dropped once counted: what
    the table publishes is a number of people, never a list of them.
    """
    actors: dict[Surface, set[int]] = {}
    gestures: dict[Surface, int] = {}

    for trace in reading.traces:
        surface = SURFACE_OF[trace.action]
        actors.setdefault(surface, set()).add(trace.actor_id)
        gestures[surface] = gestures.get(surface, 0) + trace.gestures

    people = {surface: len(ids) for surface, ids in actors.items()}

    # The three the log does not carry arrive already counted: their own
    # tables know how many took part, and nothing names them here either.
    for surface in Surface.unlogged():
        tally = reading.tally_of(surface)
        people[surface] = tally.people
        gestures[surface] = tally.gestures

    return people, gestures
