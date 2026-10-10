"""Who a gesture on a mission concerns."""

from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.projects.domain.repositories.project_assignee_repository import (
    ProjectAssigneeRepository,
)


async def people_on(assignees: ProjectAssigneeRepository, project_id: int) -> list[int]:
    """Everyone declared on a mission, at whichever title.

    Leads first, technical leads after, contributors last: the order the lines
    come out in, and someone holding several titles is told once — the fan-out
    sees to that.

    A technical lead is told like the others, and that is the point of the
    title: they are named to be called when the service breaks, so a mission
    that moves phase, goes, or gets an update is exactly what they asked to
    hear about.
    """
    return [
        *await assignees.list_for_project(project_id, ProjectRole.LEAD),
        *await assignees.list_for_project(project_id, ProjectRole.TECH_LEAD),
        *await assignees.list_for_project(project_id, ProjectRole.CONTRIBUTOR),
    ]
