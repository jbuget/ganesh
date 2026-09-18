"""Commands for assigning contributors."""

from dataclasses import dataclass

from src.modules.projects.domain.entities.project_role import ProjectRole


@dataclass(frozen=True)
class AssignmentCommand:
    """Adding or removing a contributor on a mission."""

    actor_id: int
    project_id: int
    member_id: int
    role: ProjectRole = ProjectRole.CONTRIBUTOR
