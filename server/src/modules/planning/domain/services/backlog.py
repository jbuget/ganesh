"""What the backlog is made of, and in what order it is served.

Nothing here is stored: the order is read from what the team already tells the
board — how urgent a mission is, how far along it is, where its card sits in
its column. One ordering, one place it is decided, and the plan reflects the
board rather than competing with it.

A what-if overrides that reading for the length of one request, and writes
nothing down.
"""

from collections.abc import Iterable, Mapping, Sequence

from src.modules.projects.domain.entities.project import (
    Project,
    ProjectPriority,
    ProjectStatus,
)
from src.modules.projects.domain.services.project_cost import split_delivered

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


def still_to_build(missions: Iterable[Project]) -> list[Project]:
    """What the plan steers: missions being built, not ones being kept alive.

    A work package stands on its own line: it carries its own estimate and its
    own people, and folding it into its parent would place the same days twice.

    What the plan asks of a mission is whether it carries a phase, never
    whether the board draws it. The two answered alike while the board drew
    every mission that had one; now that activities are out of the board and
    into the estimates, asking the board would quietly drop from the plan the
    very lines that carry what is left to build.
    """
    return [
        mission
        for mission in missions
        if mission.carries_a_phase and mission.status is not ProjectStatus.OPERATIONS
    ]


def remaining_build(
    estimated_days: float | None,
    delivered_by_status: Mapping[ProjectStatus | None, float],
    forecast_days: float,
) -> float | None:
    """Build left to place on a mission.

    The estimate, less what has been delivered on the build, less what has
    already been forecast by hand: a forecast is a piece of the plan somebody
    made, and planning it again would book the same days twice.

    None when nobody estimated it: a mission with no volume is not a mission
    with nothing left to do, and the plan must be able to say which it is.
    """
    if estimated_days is None:
        return None

    cost = split_delivered(delivered_by_status, estimated_days=estimated_days)
    return round(max(0.0, estimated_days - cost.build_days - forecast_days), 2)


def staffed(
    assigned: Mapping[int, list[int]], supposed: Mapping[int, list[int]]
) -> dict[int, list[int]]:
    """Who the work may be placed on, the hypothesis having its say.

    A mission the hypothesis names takes the people it names, and only them:
    naming nobody is how one asks what happens if a mission is left unstaffed.
    Missions it does not name keep the team they actually have.
    """
    return {**assigned, **supposed}
