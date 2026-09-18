"""Structural rules of the reference list."""

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
