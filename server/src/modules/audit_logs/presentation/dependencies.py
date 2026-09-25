"""Wiring of the audit log reads."""

from fastapi import Depends

from src.modules.audit_logs.application.use_cases.list_audit_log import (
    ListAuditLogUseCase,
)
from src.modules.audit_logs.application.use_cases.list_month_audit_log import (
    ListMonthAuditLogUseCase,
)
from src.modules.audit_logs.application.use_cases.list_project_audit_log import (
    ListProjectAuditLogUseCase,
)
from src.modules.audit_logs.application.use_cases.list_touched_projects import (
    ListTouchedProjectsUseCase,
)
from src.modules.audit_logs.application.use_cases.list_user_audit_log import (
    ListUserAuditLogUseCase,
)
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.entries.presentation.dependencies import (
    get_audit_log_repository,
    get_project_repository,
    get_user_repository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository


def get_project_audit_log_use_case(
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
    users: UserRepository = Depends(get_user_repository),
) -> ListProjectAuditLogUseCase:
    return ListProjectAuditLogUseCase(audit_logs=audit_logs, users=users)


def get_month_audit_log_use_case(
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
) -> ListMonthAuditLogUseCase:
    return ListMonthAuditLogUseCase(
        audit_logs=audit_logs, users=users, projects=projects
    )


def get_user_audit_log_use_case(
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
) -> ListUserAuditLogUseCase:
    return ListUserAuditLogUseCase(
        audit_logs=audit_logs, users=users, projects=projects
    )


def get_audit_log_use_case(
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
) -> ListAuditLogUseCase:
    return ListAuditLogUseCase(audit_logs=audit_logs, users=users, projects=projects)


def get_touched_projects_use_case(
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> ListTouchedProjectsUseCase:
    return ListTouchedProjectsUseCase(audit_logs=audit_logs)
