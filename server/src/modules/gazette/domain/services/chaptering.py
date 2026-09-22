"""Gathering a month's movements under the projects they are about.

Nothing is added and nothing is dropped: the same facts, read by project
instead of by the clock. Within a chapter the clock still runs, which is what
makes it a chronicle rather than a list.
"""

from collections.abc import Sequence
from datetime import datetime

from src.modules.gazette.domain.entities.chapter import Chapter, ChapterOf
from src.modules.gazette.domain.entities.movement import Movement, MovementKind

#: What a chapter about no project is sorted as: after everything else,
#: whenever it happened. Who joined the team is context around the month's
#: work rather than work itself, and opening on it would bury the month.
_LAST = datetime.max

#: What the company asked for. Told apart from the projects, because a need
#: is not a mission — the feature rests on not confusing the two — and before
#: the team, because it is still the month's work.
_ABOUT_A_NEED = frozenset(
    {
        MovementKind.REQUEST_FILED,
        MovementKind.REQUEST_ACCEPTED,
        MovementKind.REQUEST_REJECTED,
        MovementKind.REQUEST_DEFERRED,
        MovementKind.REQUEST_CONVERTED,
    }
)


def into_chapters(movements: Sequence[Movement]) -> list[Chapter]:
    """The month, one chapter per project, then the needs, then the team.

    A work package has no chapter of its own: its month is part of its
    project's month. Chapters open in the order their projects first appear,
    a project counting its packages' movements as its own for that — the
    chronicle keeps its chronological spine, one step up.
    """
    gathered: dict[int, list[Movement]] = {}
    labels: dict[int, str] = {}
    needs: list[Movement] = []
    teamless: list[Movement] = []

    for movement in movements:
        if movement.kind in _ABOUT_A_NEED:
            needs.append(movement)
            continue
        if movement.project_id is None:
            teamless.append(movement)
            continue

        # A package is told under its project. Its own name stays on the
        # movement, so the line can say which lot it was about.
        told_under = movement.parent_id or movement.project_id
        gathered.setdefault(told_under, []).append(movement)

        if movement.parent_id is None:
            labels[told_under] = movement.subject
        elif movement.parent_label is not None:
            labels.setdefault(told_under, movement.parent_label)

    chapters = [
        Chapter(
            of=ChapterOf.PROJECT,
            project_id=project_id,
            label=labels.get(project_id),
            movements=told,
        )
        for project_id, told in gathered.items()
    ]
    chapters.sort(key=_opens_on)

    if needs:
        chapters.append(
            Chapter(of=ChapterOf.REQUESTS, project_id=None, label=None, movements=needs)
        )
    if teamless:
        chapters.append(
            Chapter(of=ChapterOf.TEAM, project_id=None, label=None, movements=teamless)
        )
    return chapters


def _opens_on(chapter: Chapter) -> datetime:
    """The first thing that happened in a chapter."""
    return min((movement.at for movement in chapter.movements), default=_LAST)
