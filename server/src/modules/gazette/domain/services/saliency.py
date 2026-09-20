"""The rules that decide what a month is worth underlining.

They are rules, written down and tested, because the alternative is a model
asked to « souligner ce qui ressort » — and a model asked to underline always
underlines something, including the month nothing happened.
"""

from collections.abc import Mapping, Sequence
from datetime import date

from src.modules.gazette.domain.entities.highlight import Highlight, HighlightKind
from src.modules.gazette.domain.entities.movement import Movement, MovementKind
from src.modules.gazette.domain.services.month_window import last_day
from src.modules.projects.domain.entities.project import Project, ProjectStatus

#: The rules in the order a numéro reads them: what was achieved, then what
#: went back, then what was given up on, then what is owed and late.
_ORDER = list(HighlightKind)


def find_highlights(
    month: date,
    movements: Sequence[Movement],
    projects: Mapping[int, Project],
) -> list[Highlight]:
    """What stands out in a month, each mission underlined once per fact."""
    found = [
        *_from_movements(movements, projects),
        *_overdue(month, projects),
    ]
    return sorted(
        _once(found),
        key=lambda highlight: (_ORDER.index(highlight.kind), highlight.label),
    )


def _from_movements(
    movements: Sequence[Movement], projects: Mapping[int, Project]
) -> list[Highlight]:
    """The facts that stand out in what the month did."""
    highlights = []
    for movement in movements:
        kind = _stands_out(movement, projects)
        if kind is not None and movement.project_id is not None:
            highlights.append(
                Highlight(
                    kind=kind,
                    project_id=movement.project_id,
                    label=movement.subject,
                )
            )
    return highlights


def _stands_out(
    movement: Movement, projects: Mapping[int, Project]
) -> HighlightKind | None:
    if movement.kind is MovementKind.WENT_LIVE:
        return HighlightKind.WENT_LIVE
    if movement.kind is MovementKind.PHASE_STEPPED_BACK:
        return HighlightKind.PHASE_STEPPED_BACK
    if movement.kind is MovementKind.PROJECT_ARCHIVED and _never_delivered(
        movement, projects
    ):
        return HighlightKind.ARCHIVED_BEFORE_DELIVERY
    return None


def _never_delivered(movement: Movement, projects: Mapping[int, Project]) -> bool:
    """Whether a mission left the list without the work ever having run.

    Leaving once it runs is a retirement, and steering reads that as an end
    rather than as a loss.
    """
    project = projects.get(movement.project_id) if movement.project_id else None
    return project is not None and project.status is not ProjectStatus.OPERATIONS


def _overdue(month: date, projects: Mapping[int, Project]) -> list[Highlight]:
    """The missions whose announced date went by without the work running.

    Read against the end of the month covered, never against today: a numéro
    reopened a year later must say what it said the day it was published.
    """
    closing = last_day(month)
    return [
        Highlight(
            kind=HighlightKind.GO_LIVE_OVERDUE, project_id=id_, label=project.label
        )
        for id_, project in projects.items()
        if project.is_active
        and project.status is not ProjectStatus.OPERATIONS
        and project.go_live_date is not None
        and project.go_live_date <= closing
    ]


def _once(highlights: Sequence[Highlight]) -> list[Highlight]:
    """The same fact about the same mission, underlined once.

    Two phase moves back in one month is one worry; printing it twice would
    make a hesitant month look like a failing one.
    """
    return list({(h.kind, h.project_id): h for h in highlights}.values())
