"""Wiring of the teammate use cases."""

from fastapi import Depends

from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.entries.presentation.dependencies import (
    get_audit_log_repository,
    get_entry_repository,
    get_month_repository,
    get_project_repository,
    get_user_repository,
)
from src.modules.months.domain.repositories.month_repository import MonthRepository
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.notifications.presentation.dependencies import (
    get_notification_delivery,
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
from src.modules.users.application.use_cases.change_user_role import (
    ChangeUserRoleUseCase,
)
from src.modules.users.application.use_cases.get_user_record import GetUserRecordUseCase
from src.modules.users.application.use_cases.list_users import ListUsersUseCase
from src.modules.users.application.use_cases.set_user_active import SetUserActiveUseCase
from src.modules.users.application.use_cases.update_user_identity import (
    UpdateUserIdentityUseCase,
)
from src.modules.users.domain.repositories.user_repository import UserRepository


def get_list_users_use_case(
    users: UserRepository = Depends(get_user_repository),
) -> ListUsersUseCase:
    return ListUsersUseCase(users=users)


def get_change_role_use_case(
    users: UserRepository = Depends(get_user_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
    notifications: NotificationDelivery = Depends(get_notification_delivery),
) -> ChangeUserRoleUseCase:
    return ChangeUserRoleUseCase(
        users=users, audit_logs=audit_logs, notifications=notifications
    )


def get_set_user_active_use_case(
    users: UserRepository = Depends(get_user_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
    notifications: NotificationDelivery = Depends(get_notification_delivery),
) -> SetUserActiveUseCase:
    return SetUserActiveUseCase(
        users=users, audit_logs=audit_logs, notifications=notifications
    )


def get_update_user_identity_use_case(
    users: UserRepository = Depends(get_user_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> UpdateUserIdentityUseCase:
    return UpdateUserIdentityUseCase(users=users, audit_logs=audit_logs)


def get_user_record_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    assignees: ProjectAssigneeRepository = Depends(get_project_assignee_repository),
    entries: EntryRepository = Depends(get_entry_repository),
    months: MonthRepository = Depends(get_month_repository),
) -> GetUserRecordUseCase:
    return GetUserRecordUseCase(
        users=users,
        projects=projects,
        assignees=assignees,
        entries=entries,
        months=months,
    )
