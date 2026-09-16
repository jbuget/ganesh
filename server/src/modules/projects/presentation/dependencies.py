"""Cablage des use cases du referentiel."""

from fastapi import Depends

from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.entries.presentation.dependencies import (
    get_audit_log_repository,
    get_entry_repository,
    get_project_repository,
    get_user_repository,
)
from src.modules.projects.application.use_cases.change_project_status import (
    ChangeProjectStatusUseCase,
)
from src.modules.projects.application.use_cases.create_project import (
    CreateProjectUseCase,
)
from src.modules.projects.application.use_cases.delete_project import (
    DeleteProjectUseCase,
)
from src.modules.projects.application.use_cases.get_board import GetBoardUseCase
from src.modules.projects.application.use_cases.import_projects import (
    ImportProjectsUseCase,
)
from src.modules.projects.application.use_cases.list_projects import ListProjectsUseCase
from src.modules.projects.application.use_cases.move_project import MoveProjectUseCase
from src.modules.projects.application.use_cases.update_project import (
    UpdateProjectUseCase,
)
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
    entries: EntryRepository = Depends(get_entry_repository),
) -> ListProjectsUseCase:
    return ListProjectsUseCase(projects=projects, entries=entries)


def get_delete_project_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    entries: EntryRepository = Depends(get_entry_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> DeleteProjectUseCase:
    return DeleteProjectUseCase(
        users=users, projects=projects, entries=entries, audit_logs=audit_logs
    )


def get_update_project_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> UpdateProjectUseCase:
    return UpdateProjectUseCase(users=users, projects=projects, audit_logs=audit_logs)


def get_import_projects_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> ImportProjectsUseCase:
    return ImportProjectsUseCase(users=users, projects=projects, audit_logs=audit_logs)


def get_board_use_case(
    projects: ProjectRepository = Depends(get_project_repository),
    entries: EntryRepository = Depends(get_entry_repository),
    users: UserRepository = Depends(get_user_repository),
) -> GetBoardUseCase:
    return GetBoardUseCase(projects=projects, entries=entries, users=users)


def get_move_project_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> MoveProjectUseCase:
    return MoveProjectUseCase(users=users, projects=projects, audit_logs=audit_logs)
