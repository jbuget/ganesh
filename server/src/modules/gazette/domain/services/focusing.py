"""Choosing the projects a month is told through.

By rule, like everything else the gazette underlines: a model asked to pick
« the flagship project » picks one even the month nothing happened, and picks
differently each time it is asked. The rule reads what the register holds —
did it go live, how much was written on it, how much time went into it — and
the model is only handed the winners to tell.
"""

from collections.abc import Mapping, Sequence
from functools import partial

from src.modules.entries.domain.entities.entry import Entry
from src.modules.gazette.domain.entities.focus import ProjectFocus
from src.modules.gazette.domain.entities.movement import Movement, MovementKind
from src.modules.projects.domain.entities.project import Project, ProjectKind
from src.modules.projects.domain.entities.project_update import ProjectUpdate

#: How many projects a month is told through. More than three and none of them
#: is a flagship any more.
SPOTLIGHT_LIMIT = 3

#: How many further projects are read for what the rest of the month held.
BACKGROUND_LIMIT = 8

_PHASE_MOVES = {
    MovementKind.PHASE_ADVANCED,
    MovementKind.PHASE_STEPPED_BACK,
    MovementKind.WENT_LIVE,
}


def owner_of(project_id: int, projects: Mapping[int, Project]) -> int | None:
    """The project a piece of the month is told under.

    A work package is told inside its project; off-project work is told under
    none, and neither is anything the reference list can no longer name.
    """
    project = projects.get(project_id)
    if project is None or project.kind is ProjectKind.OFF_PROJECT:
        return None
    parent = projects.get(project.parent_id) if project.parent_id else None
    return parent.id if parent is not None else project_id


def pick_focus(
    movements: Sequence[Movement],
    updates: Sequence[ProjectUpdate],
    entries: Sequence[Entry],
    projects: Mapping[int, Project],
    limit: int = SPOTLIGHT_LIMIT,
) -> list[ProjectFocus]:
    """The projects of the month, most telling first.

    A work package is told inside its project, as everywhere else in the
    gazette. Off-project work is never a project of the month, and a project
    with nothing written on it that did not go live has no story to tell.
    """

    root = partial(owner_of, projects=projects)

    went_live: set[int] = set()
    phase_moves: dict[int, int] = {}
    for movement in movements:
        if movement.kind not in _PHASE_MOVES or movement.project_id is None:
            continue
        owner = root(movement.project_id)
        if owner is None:
            continue
        phase_moves[owner] = phase_moves.get(owner, 0) + 1
        if movement.kind is MovementKind.WENT_LIVE:
            went_live.add(owner)

    posted: dict[int, int] = {}
    for update in updates:
        owner = root(update.project_id)
        if not update.is_deleted and owner is not None:
            posted[owner] = posted.get(owner, 0) + 1

    days: dict[int, float] = {}
    people: dict[int, set[int]] = {}
    for entry in entries:
        owner = root(entry.project_id)
        if owner is not None:
            days[owner] = days.get(owner, 0.0) + float(entry.value)
            people.setdefault(owner, set()).add(entry.user_id)

    candidates = [
        ProjectFocus(
            project_id=owner,
            label=projects[owner].label,
            status=projects[owner].status,
            went_live=owner in went_live,
            phase_moves=phase_moves.get(owner, 0),
            updates_posted=posted.get(owner, 0),
            days_declared=days.get(owner, 0.0),
            contributors=len(people.get(owner, set())),
        )
        for owner in {*went_live, *posted}
    ]
    told = [focus for focus in candidates if focus.has_material]
    told.sort(
        key=lambda focus: (
            not focus.went_live,
            -focus.updates_posted,
            -focus.days_declared,
            -focus.phase_moves,
            focus.label,
        )
    )
    return told[:limit]
