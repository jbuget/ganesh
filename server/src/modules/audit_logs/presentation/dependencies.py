"""Wiring of the audit log reads."""

from fastapi import Depends

from src.modules.audit_logs.application.use_cases.list_project_audit_log import (
    ListProjectAuditLogUseCase,
)
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.entries.presentation.dependencies import (
    get_audit_log_repository,
    get_user_repository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository


def get_project_audit_log_use_case(
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
    users: UserRepository = Depends(get_user_repository),
) -> ListProjectAuditLogUseCase:
    return ListProjectAuditLogUseCase(audit_logs=audit_logs, users=users)
