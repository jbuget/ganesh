"""Structural rules of the reference list."""

from dataclasses import replace

from src.modules.projects.domain.entities.project import Project, ProjectKind
from src.shared.exceptions.domain_exceptions import ValidationError


def ensure_can_be_parent(parent: Project) -> None:
    """Refuses attaching anything under something other than a project.

    The hierarchy deliberately stops at two levels: a project, its work
    packages. A third level would complicate entry and totals without giving
    steering anything.
    """
    if parent.kind is ProjectKind.WORK_PACKAGE:
        raise ValidationError(
            f"« {parent.label} » is already a sub-project: "
            "the hierarchy stops at two levels."
        )
    if parent.kind is ProjectKind.OFF_PROJECT:
        raise ValidationError(
            f"« {parent.label} » is off-project work: " "it cannot carry a sub-project."
        )


def ensure_carries_no_own_category(project: Project) -> None:
    """Refuses a strategic axis of its own to a work package.

    The axis qualifies the product, not a slice of it. Two work packages of one
    project claiming two axes would leave the project itself with none, and its
    totals would no longer add up to anything. A package that genuinely shifts
    the axis shifts the project's: that is where it is changed, for the whole
    project and its packages at once.
    """
    if project.kind is ProjectKind.WORK_PACKAGE and project.category is not None:
        raise ValidationError(
            "A work package carries the strategic axis of its project, "
            "never an axis of its own."
        )


def with_resolved_category(project: Project, parent: Project | None) -> Project:
    """The mission as it reads: a work package shows its project's axis.

    Nothing is written. The column stays empty on the package, so the axis
    follows its project by construction — there is no copy to keep in step, and
    therefore no rule to replay when the project changes, when a package is
    detached, or when one is deleted.

    A package whose project is out of reach reads without an axis rather than
    with an invented one.
    """
    if project.kind is not ProjectKind.WORK_PACKAGE:
        return project
    return replace(project, category=parent.category if parent else None)


def ensure_can_be_attached(
    project: Project, parent: Project, sub_projects: int
) -> None:
    """Refuses turning a mission into a work package of another one.

    Rearranging the reference list is ordinary: one declares two projects
    before realising they are two slices of a single service. What the rules
    guard is that the move loses nothing — no level the screens cannot read, no
    catalogue card gone without anyone saying so.
    """
    if project.id == parent.id:
        raise ValidationError(f"« {project.label} » cannot be attached to itself.")
    if project.is_off_project:
        raise ValidationError(
            f"« {project.label} » is off-project work: "
            "it is not a slice of a project."
        )
    if sub_projects > 0:
        raise ValidationError(
            f"« {project.label} » carries sub-projects of its own: "
            "the hierarchy stops at two levels. Detach them first."
        )
    if project.is_published:
        raise ValidationError(
            f"« {project.label} » is published in the catalogue: "
            "unpublish it before attaching it, or the card disappears."
        )
    ensure_can_be_parent(parent)


def ensure_can_be_detached(project: Project) -> None:
    """Refuses detaching what is not attached to anything."""
    if project.kind is not ProjectKind.WORK_PACKAGE:
        raise ValidationError(f"« {project.label} » is not a sub-project.")
