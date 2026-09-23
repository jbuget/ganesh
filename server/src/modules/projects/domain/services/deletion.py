"""When a mission may be deleted."""

from src.modules.projects.domain.entities.project import Project
from src.shared.exceptions.domain_exceptions import ForbiddenActionError


def deletion_obstacle(project: Project, entries: int, sub_projects: int) -> str | None:
    """What stands in the way of deleting the mission, or nothing.

    A mission never used may disappear: it was a slip in the reference list.
    Once it carries time, deleting it would destroy declared work — we archive
    instead, which takes it out of the lists without losing anything. A
    project that was cut into packages keeps them: the deletion does not go
    down the tree, and the time they carry is not counted here. And a
    published mission is an address somebody may have kept: it is unpublished
    first, deliberately, rather than dropped off the catalogue by a deletion
    aimed at something else.

    Time declared is said before the publication, because its answer —
    archiving — is the whole answer rather than a first step: the catalogue
    keeps the card and marks it archived, so nothing is lost and nothing is
    dropped from waat.tools. Sending somebody to unpublish first would add a
    step that changes nothing.

    The conditions are written once, here: the screens ask whether the action
    may be offered, the guard refuses it when it is attempted anyway, and
    neither may answer differently from the other.
    """
    if sub_projects > 0:
        return (
            f"« {project.label} » carries {sub_projects} sub-project(s): "
            "deal with those first."
        )
    if entries > 0:
        return (
            f"« {project.label} » already carries {entries} time entry/entries: "
            "you can archive it, not delete it."
        )
    if project.is_published:
        return (
            f"« {project.label} » is published in the catalogue: unpublish it "
            "first, or its card would leave waat.tools with nobody saying so."
        )
    return None


def can_be_deleted(project: Project, entries: int, sub_projects: int) -> bool:
    """Whether the mission may disappear, asked without provoking the refusal."""
    return deletion_obstacle(project, entries, sub_projects) is None


def ensure_can_be_deleted(project: Project, entries: int, sub_projects: int) -> None:
    """Refuses deletion as soon as the mission has been used."""
    obstacle = deletion_obstacle(project, entries, sub_projects)
    if obstacle is not None:
        raise ForbiddenActionError(obstacle)
