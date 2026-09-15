"""Cablage des use cases du referentiel."""

from fastapi import Depends

from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.entries.presentation.dependencies import (
    get_audit_log_repository,
    get_project_repository,
    get_user_repository,
)
from src.modules.projects.application.use_cases.change_project_status import (
    ChangeProjectStatusUseCase,
)
from src.modules.projects.application.use_cases.create_project import (
    CreateProjectUseCase,
)
from src.modules.projects.application.use_cases.list_projects import ListProjectsUseCase
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository


def get_create_project_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> CreateProjectUseCase:
    return CreateProjectUseCase(users=users, projects=projects, audit_logs=audit_logs)


def get_change_status_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> ChangeProjectStatusUseCase:
    return ChangeProjectStatusUseCase(
        users=users, projects=projects, audit_logs=audit_logs
    )


def get_list_projects_use_case(
    projects: ProjectRepository = Depends(get_project_repository),
) -> ListProjectsUseCase:
    return ListProjectsUseCase(projects=projects)
