"""Who a gesture on a mission concerns."""

from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.projects.domain.repositories.project_assignee_repository import (
    ProjectAssigneeRepository,
)


async def people_on(assignees: ProjectAssigneeRepository, project_id: int) -> list[int]:
    """Everyone declared on a mission, at whichever title.

    Leads first, contributors after: the order the lines come out in, and
    someone holding both is told once — the fan-out sees to that.
    """
    return [
        *await assignees.list_for_project(project_id, ProjectRole.LEAD),
        *await assignees.list_for_project(project_id, ProjectRole.CONTRIBUTOR),
    ]
