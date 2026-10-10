"""What is not worth telling a reader from outside the team.

A project opened and closed within the month, without a single update, tells
nothing: it is a mistake put right, a test, a duplicate. Handed to a model it
gets a sentence, and a sentence about nothing is noise in front of the ones that
matter. The register keeps it — the tally counts it and the chronicle lists it —
but the texts written over the month leave it out.
"""

from collections.abc import Sequence

from src.modules.gazette.domain.entities.movement import Movement, MovementKind
from src.modules.projects.domain.entities.project_update import ProjectUpdate


def short_lived_projects(
    movements: Sequence[Movement], updates: Sequence[ProjectUpdate]
) -> frozenset[int]:
    """The projects created and archived in the month with nothing written on them."""
    created = {
        m.project_id
        for m in movements
        if m.kind is MovementKind.PROJECT_CREATED and m.project_id is not None
    }
    archived = {
        m.project_id
        for m in movements
        if m.kind is MovementKind.PROJECT_ARCHIVED and m.project_id is not None
    }
    written_on = {u.project_id for u in updates if not u.is_deleted}
    return frozenset((created & archived) - written_on)
