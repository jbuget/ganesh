"""Wiring of the workload plan use case."""

from fastapi import Depends

from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.entries.presentation.dependencies import (
    get_entry_repository,
    get_project_repository,
    get_user_repository,
)
from src.modules.planning.application.use_cases.get_workload_plan import (
    GetWorkloadPlanUseCase,
)
from src.modules.projects.domain.repositories.project_assignee_repository import (
    ProjectAssigneeRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.presentation.dependencies import (
    get_project_assignee_repository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository


def get_workload_plan_use_case(
    projects: ProjectRepository = Depends(get_project_repository),
    entries: EntryRepository = Depends(get_entry_repository),
    assignees: ProjectAssigneeRepository = Depends(get_project_assignee_repository),
    users: UserRepository = Depends(get_user_repository),
) -> GetWorkloadPlanUseCase:
    return GetWorkloadPlanUseCase(
        projects=projects, entries=entries, assignees=assignees, users=users
    )
