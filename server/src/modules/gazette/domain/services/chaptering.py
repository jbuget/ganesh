"""Gathering a month's movements under the missions they are about.

Nothing is added and nothing is dropped: the same facts, read by mission
instead of by the clock. Within a chapter the clock still runs, which is what
makes it a chronicle rather than a list.
"""

from collections.abc import Sequence
from datetime import datetime

from src.modules.gazette.domain.entities.chapter import Chapter
from src.modules.gazette.domain.entities.movement import Movement

#: What a chapter about no mission is sorted as: after everything else,
#: whenever it happened. Who joined the team is context around the month's
#: work rather than work itself, and opening on it would bury the month.
_LAST = datetime.max


def into_chapters(movements: Sequence[Movement]) -> list[Chapter]:
    """The month, one chapter per mission, packages told inside their project.

    Chapters open in the order their missions first appear, a project counting
    its packages' movements as its own for that: the chronicle keeps its
    chronological spine, one step up.
    """
    own: dict[int, list[Movement]] = {}
    labels: dict[int, str] = {}
    packages: dict[int, list[int]] = {}
    parents: dict[int, int] = {}
    teamless: list[Movement] = []

    for movement in movements:
        if movement.project_id is None:
            teamless.append(movement)
            continue

        own.setdefault(movement.project_id, []).append(movement)
        labels[movement.project_id] = movement.subject

        if movement.parent_id is None:
            continue

        # A package's project opens a chapter even when nothing happened to
        # the project itself: a package read on its own would be taken for a
        # project it is not.
        parents[movement.project_id] = movement.parent_id
        own.setdefault(movement.parent_id, [])
        if movement.parent_label is not None:
            labels.setdefault(movement.parent_id, movement.parent_label)
        under = packages.setdefault(movement.parent_id, [])
        if movement.project_id not in under:
            under.append(movement.project_id)

    chapters = [
        _chapter(project_id, own, labels, packages)
        for project_id in own
        if project_id not in parents
    ]
    chapters.sort(key=lambda chapter: _opens_on(chapter))

    if teamless:
        chapters.append(Chapter(project_id=None, label=None, movements=teamless))
    return chapters


def _chapter(
    project_id: int,
    own: dict[int, list[Movement]],
    labels: dict[int, str],
    packages: dict[int, list[int]],
) -> Chapter:
    """One mission's chapter, its packages gathered under it."""
    inside = [
        _chapter(package_id, own, labels, packages)
        for package_id in packages.get(project_id, [])
    ]
    inside.sort(key=lambda chapter: _opens_on(chapter))
    return Chapter(
        project_id=project_id,
        label=labels.get(project_id),
        movements=own.get(project_id, []),
        packages=inside,
    )


def _opens_on(chapter: Chapter) -> datetime:
    """The first thing that happened in a chapter, its packages counted in."""
    moments = [movement.at for movement in chapter.movements]
    moments += [_opens_on(package) for package in chapter.packages]
    return min(moments) if moments else _LAST
