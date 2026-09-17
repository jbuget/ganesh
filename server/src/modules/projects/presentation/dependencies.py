"""Cablage des use cases du referentiel."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
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
from src.modules.projects.application.use_cases.assign_member import (
    AssignMemberUseCase,
    UnassignMemberUseCase,
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
from src.modules.projects.application.use_cases.get_project_detail import (
    GetProjectDetailUseCase,
)
from src.modules.projects.application.use_cases.import_projects import (
    ImportProjectsUseCase,
)
from src.modules.projects.application.use_cases.list_projects import ListProjectsUseCase
from src.modules.projects.application.use_cases.move_project import MoveProjectUseCase
from src.modules.projects.application.use_cases.update_project import (
    UpdateProjectUseCase,
)
from src.modules.projects.application.use_cases.update_project_detail import (
    AddProjectLinkUseCase,
    RemoveProjectLinkUseCase,
    UpdateDescriptionUseCase,
    UpdateProjectDetailUseCase,
)
from src.modules.projects.domain.repositories.project_assignee_repository import (
    ProjectAssigneeRepository,
)
from src.modules.projects.domain.repositories.project_detail_repository import (
    ProjectDetailRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_assignee_repository_impl import (
    SqlProjectAssigneeRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_detail_repository_impl import (
    SqlProjectDetailRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository


def get_project_detail_repository(
    session: AsyncSession = Depends(get_db),
) -> ProjectDetailRepository:
    return SqlProjectDetailRepository(session)


def get_project_assignee_repository(
    session: AsyncSession = Depends(get_db),
) -> ProjectAssigneeRepository:
    return SqlProjectAssigneeRepository(session)


def get_create_project_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> CreateProjectUseCase:
    return CreateProjectUseCase(users=users, projects=projects, audit_logs=audit_logs)


def get_change_status_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    details: ProjectDetailRepository = Depends(get_project_detail_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> ChangeProjectStatusUseCase:
    return ChangeProjectStatusUseCase(
        users=users, projects=projects, details=details, audit_logs=audit_logs
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
    assignees: ProjectAssigneeRepository = Depends(get_project_assignee_repository),
) -> GetBoardUseCase:
    return GetBoardUseCase(
        projects=projects, entries=entries, users=users, assignees=assignees
    )


def get_move_project_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    details: ProjectDetailRepository = Depends(get_project_detail_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> MoveProjectUseCase:
    return MoveProjectUseCase(
        users=users, projects=projects, details=details, audit_logs=audit_logs
    )


def get_assign_member_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    assignees: ProjectAssigneeRepository = Depends(get_project_assignee_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> AssignMemberUseCase:
    return AssignMemberUseCase(
        users=users, projects=projects, assignees=assignees, audit_logs=audit_logs
    )


def get_unassign_member_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    assignees: ProjectAssigneeRepository = Depends(get_project_assignee_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> UnassignMemberUseCase:
    return UnassignMemberUseCase(
        users=users, projects=projects, assignees=assignees, audit_logs=audit_logs
    )


def get_project_detail_use_case(
    projects: ProjectRepository = Depends(get_project_repository),
    details: ProjectDetailRepository = Depends(get_project_detail_repository),
    assignees: ProjectAssigneeRepository = Depends(get_project_assignee_repository),
    entries: EntryRepository = Depends(get_entry_repository),
    users: UserRepository = Depends(get_user_repository),
) -> GetProjectDetailUseCase:
    return GetProjectDetailUseCase(
        projects=projects,
        details=details,
        assignees=assignees,
        entries=entries,
        users=users,
    )


def get_update_project_detail_use_case(
    projects: ProjectRepository = Depends(get_project_repository),
    details: ProjectDetailRepository = Depends(get_project_detail_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> UpdateProjectDetailUseCase:
    return UpdateProjectDetailUseCase(
        projects=projects, details=details, audit_logs=audit_logs
    )


def get_add_project_link_use_case(
    projects: ProjectRepository = Depends(get_project_repository),
    details: ProjectDetailRepository = Depends(get_project_detail_repository),
) -> AddProjectLinkUseCase:
    return AddProjectLinkUseCase(projects=projects, details=details)


def get_remove_project_link_use_case(
    details: ProjectDetailRepository = Depends(get_project_detail_repository),
) -> RemoveProjectLinkUseCase:
    return RemoveProjectLinkUseCase(details=details)


def get_update_description_use_case(
    projects: ProjectRepository = Depends(get_project_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> UpdateDescriptionUseCase:
    return UpdateDescriptionUseCase(projects=projects, audit_logs=audit_logs)
