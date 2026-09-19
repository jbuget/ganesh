"""Turning what is known of a mission into the bar a roadmap draws.

The function is pure, and takes the day as an argument: a bar drawn for
September must not change because the test suite ran past midnight.

One rule runs through all of it — nothing is invented. What was never recorded
leaves no segment, and a stretch nobody can date is carried by the nearest
phase that is dated rather than guessed at. A roadmap that fills its own gaps
is read as fact and is not one.
"""

from collections.abc import Mapping
from datetime import date, timedelta

from src.modules.planning.domain.entities.roadmap import RoadmapSegment, SegmentKind
from src.modules.projects.domain.entities.project import ProjectStatus

#: Nominal order of the phases, to break a tie between two crossed the same day.
_PHASE_RANK: dict[ProjectStatus, int] = {
    status: rank for rank, status in enumerate(ProjectStatus)
}

_ONE_DAY = timedelta(days=1)


def draw_segments(
    *,
    status: ProjectStatus | None,
    phases_reached: Mapping[ProjectStatus, date],
    first_declared: date | None,
    last_declared: date | None,
    projected_end: date | None,
    today: date,
    window_end: date,
    is_active: bool,
) -> list[RoadmapSegment]:
    """The whole bar of one mission, in chronological order.

    `phases_reached` holds the day each phase was **first** entered, which is
    what the reference list records. Ordering it by date rather than by the
    nominal sequence is therefore right, and a mission sent back a phase still
    draws a bar that reads forwards.
    """
    lived_end = _lived_end(phases_reached, last_declared, today, is_active)
    if lived_end is None:
        return []

    runs = status is ProjectStatus.OPERATIONS
    running_from = _running_from(phases_reached, today, lived_end) if runs else None

    # A service being kept alive closes its history the day it went live: what
    # comes after is not a phase, it is a life.
    crossed = _crossed(phases_reached, before=running_from)
    lived = _lived(
        crossed,
        opens_on=first_declared,
        closes_on=(running_from - _ONE_DAY) if running_from else lived_end,
        fallback_status=status,
    )

    if running_from is not None:
        return lived + [
            RoadmapSegment(
                kind=SegmentKind.RUNNING,
                status=ProjectStatus.OPERATIONS,
                starts_on=running_from,
                # A service that runs has no end. The window's edge is where
                # the drawing stops, not where the service does.
                ends_on=max(window_end if is_active else lived_end, running_from),
            )
        ]

    projected = _projected(
        projected_end,
        after=lived[-1].ends_on if lived else None,
        today=today,
        status=status,
        is_active=is_active,
    )
    return lived + projected


def _lived_end(
    phases_reached: Mapping[ProjectStatus, date],
    last_declared: date | None,
    today: date,
    is_active: bool,
) -> date | None:
    """The last day the bar has anything true to say.

    Today for a mission still going: it is being lived right now. For one
    that left the reference list, the last day anybody declared on it — an
    archived mission must not keep growing a bar.
    """
    if is_active:
        return today
    known = [day for day in (last_declared, *phases_reached.values()) if day]
    return max(known) if known else None


def _running_from(
    phases_reached: Mapping[ProjectStatus, date], today: date, lived_end: date
) -> date:
    """The day the service went live.

    Nobody recorded it on the missions that were already running when the
    reference list was filled in. Those run from today: saying « depuis
    toujours » would draw a history that never happened.
    """
    return phases_reached.get(ProjectStatus.OPERATIONS, min(today, lived_end))


def _crossed(
    phases_reached: Mapping[ProjectStatus, date], before: date | None
) -> list[tuple[ProjectStatus, date]]:
    """The phases the mission went through, oldest first."""
    kept = [
        (status, day)
        for status, day in phases_reached.items()
        if before is None or day < before
    ]
    return sorted(kept, key=lambda crossing: (crossing[1], _PHASE_RANK[crossing[0]]))


def _lived(
    crossed: list[tuple[ProjectStatus, date]],
    opens_on: date | None,
    closes_on: date,
    fallback_status: ProjectStatus | None,
) -> list[RoadmapSegment]:
    """What happened, one segment per phase.

    A mission nobody ever moved has no crossing to draw and still has a past:
    it gets one segment, under the phase it sits in today.
    """
    if not crossed:
        if opens_on is None or opens_on > closes_on:
            return []
        return [
            RoadmapSegment(
                kind=SegmentKind.LIVED,
                status=fallback_status,
                starts_on=opens_on,
                ends_on=closes_on,
            )
        ]

    # Time declared before the first phase was recorded belongs to the bar all
    # the same. Which phase it was spent in was never written down, so it is
    # carried by the first one known rather than made up.
    starts = [min(crossed[0][1], opens_on) if opens_on else crossed[0][1]]
    starts += [day for _, day in crossed[1:]]
    ends = [day - _ONE_DAY for _, day in crossed[1:]] + [closes_on]

    return [
        RoadmapSegment(
            kind=SegmentKind.LIVED, status=status, starts_on=start, ends_on=end
        )
        for (status, _), start, end in zip(crossed, starts, ends)
        # Two phases crossed the same day leave an empty stretch between them,
        # and an empty stretch is not a segment.
        if start <= end
    ]


def _projected(
    projected_end: date | None,
    after: date | None,
    today: date,
    status: ProjectStatus | None,
    is_active: bool,
) -> list[RoadmapSegment]:
    """What the projection supposes, and never anything more.

    An archived mission is not projected: the plan drops it, and so does this.
    """
    if projected_end is None or not is_active:
        return []

    starts_on = after + _ONE_DAY if after else today
    if projected_end < starts_on:
        return []

    return [
        RoadmapSegment(
            kind=SegmentKind.PROJECTED,
            status=status,
            starts_on=starts_on,
            ends_on=projected_end,
        )
    ]
