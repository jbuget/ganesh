"""Cablage des use cases collaborateurs."""

from fastapi import Depends

from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.entries.presentation.dependencies import (
    get_audit_log_repository,
    get_user_repository,
)
from src.modules.users.application.use_cases.change_user_role import (
    ChangeUserRoleUseCase,
)
from src.modules.users.application.use_cases.list_users import ListUsersUseCase
from src.modules.users.domain.repositories.user_repository import UserRepository


def get_list_users_use_case(
    users: UserRepository = Depends(get_user_repository),
) -> ListUsersUseCase:
    return ListUsersUseCase(users=users)


def get_change_role_use_case(
    users: UserRepository = Depends(get_user_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> ChangeUserRoleUseCase:
    return ChangeUserRoleUseCase(users=users, audit_logs=audit_logs)
