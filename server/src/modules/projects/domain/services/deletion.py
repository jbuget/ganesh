"""When a mission may be deleted."""

from src.modules.projects.domain.entities.project import Project
from src.shared.exceptions.domain_exceptions import ForbiddenActionError


def ensure_can_be_deleted(project: Project, entries: int, sub_projects: int) -> None:
    """Refuses deletion as soon as the mission has been used.

    A mission never used may disappear: it was a slip in the reference list.
    Once it carries time, deleting it would destroy declared work — we archive
    instead, which takes it out of the lists without losing anything.
    """
    if sub_projects > 0:
        raise ForbiddenActionError(
            f"« {project.label} » carries {sub_projects} sub-project(s): "
            "deal with those first."
        )
    if entries > 0:
        raise ForbiddenActionError(
            f"« {project.label} » already carries {entries} time entry/entries: "
            "you can archive it, not delete it."
        )
