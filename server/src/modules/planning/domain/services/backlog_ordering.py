"""The order the backlog is served in.

Nothing here is stored: the order is read from what the team already tells the
board — how urgent a mission is, how far along it is, where its card sits in
its column. One ordering, one place it is decided, and the plan reflects the
board rather than competing with it.

A what-if overrides that reading for the length of one request, and writes
nothing down.
"""

from collections.abc import Iterable, Sequence

from src.modules.projects.domain.entities.project import (
    Project,
    ProjectPriority,
    ProjectStatus,
)

#: Most urgent first. A mission nobody ranked comes after every ranked one:
#: not having placed it against the others must not push it ahead of them.
_PRIORITIES: list[ProjectPriority] = list(ProjectPriority)
_PRIORITY_RANK: dict[ProjectPriority | None, int] = {
    priority: rank for rank, priority in enumerate(_PRIORITIES)
}
_PRIORITY_RANK[None] = len(_PRIORITIES)

#: Nominal order of the phases, to tell how far along a mission is.
_PHASES: list[ProjectStatus] = list(ProjectStatus)
_PHASE_RANK: dict[ProjectStatus, int] = {
    status: rank for rank, status in enumerate(_PHASES)
}


def backlog_rank(mission: Project) -> tuple[int, int, int, str]:
    """Where a mission sits in the queue.

    The most urgent first; at equal urgency, what is furthest along, because
    finishing beats starting; then the rank the team gave the card in its
    column; then the label, so that two alike never swap from one load to the
    next.
    """
    phase = _PHASE_RANK.get(mission.status, 0) if mission.status else 0
    return (
        _PRIORITY_RANK[mission.priority],
        -phase,
        mission.position,
        mission.label,
    )


def order_backlog(missions: Iterable[Project]) -> list[Project]:
    """The missions in the order the projection must serve them."""
    return sorted(missions, key=backlog_rank)


def apply_explicit_order(
    missions: Iterable[Project], order: Sequence[int]
) -> list[Project]:
    """The same missions, with the order asked for placed on top.

    What the hypothesis does not name keeps the derived order behind it: a
    what-if moves a card or two, and must not force the whole backlog to be
    respelled. An id naming no mission is ignored rather than refused: a
    hypothesis typed against a mission archived meanwhile still reads.
    """
    derived = order_backlog(missions)
    by_id = {mission.id: mission for mission in derived}

    named = [
        by_id[project_id] for project_id in dict.fromkeys(order) if project_id in by_id
    ]
    chosen = {mission.id for mission in named}
    return named + [mission for mission in derived if mission.id not in chosen]
