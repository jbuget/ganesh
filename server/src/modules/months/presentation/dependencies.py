"""Cablage des use cases de gestion des mois."""

from fastapi import Depends

from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.entries.presentation.dependencies import (
    get_audit_log_repository,
    get_month_repository,
    get_user_repository,
)
from src.modules.months.application.use_cases.reopen_month import ReopenMonthUseCase
from src.modules.months.application.use_cases.validate_month import ValidateMonthUseCase
from src.modules.months.domain.repositories.month_repository import MonthRepository
from src.modules.users.domain.repositories.user_repository import UserRepository


def get_validate_month_use_case(
    users: UserRepository = Depends(get_user_repository),
    months: MonthRepository = Depends(get_month_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> ValidateMonthUseCase:
    return ValidateMonthUseCase(users=users, months=months, audit_logs=audit_logs)


def get_reopen_month_use_case(
    users: UserRepository = Depends(get_user_repository),
    months: MonthRepository = Depends(get_month_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> ReopenMonthUseCase:
    return ReopenMonthUseCase(users=users, months=months, audit_logs=audit_logs)
