"""Cablage des use cases de saisie."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.audit_logs.infrastructure.database.repositories.audit_log_repository_impl import (
    SqlAuditLogRepository,
)
from src.modules.entries.application.use_cases.clear_entry import ClearEntryUseCase
from src.modules.entries.application.use_cases.get_month_grid import GetMonthGridUseCase
from src.modules.entries.application.use_cases.remove_mission_from_month import (
    RemoveMissionFromMonthUseCase,
)
from src.modules.entries.application.use_cases.set_entry import SetEntryUseCase
from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.entries.infrastructure.database.repositories.entry_repository_impl import (
    SqlEntryRepository,
)
from src.modules.months.domain.repositories.month_repository import MonthRepository
from src.modules.months.infrastructure.database.repositories.month_repository_impl import (
    SqlMonthRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_repository_impl import (
    SqlProjectRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)


def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return SqlUserRepository(session)


def get_project_repository(
    session: AsyncSession = Depends(get_db),
) -> ProjectRepository:
    return SqlProjectRepository(session)


def get_entry_repository(session: AsyncSession = Depends(get_db)) -> EntryRepository:
    return SqlEntryRepository(session)


def get_month_repository(session: AsyncSession = Depends(get_db)) -> MonthRepository:
    return SqlMonthRepository(session)


def get_audit_log_repository(
    session: AsyncSession = Depends(get_db),
) -> AuditLogRepository:
    return SqlAuditLogRepository(session)


def get_set_entry_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    entries: EntryRepository = Depends(get_entry_repository),
    months: MonthRepository = Depends(get_month_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> SetEntryUseCase:
    return SetEntryUseCase(
        users=users,
        projects=projects,
        entries=entries,
        months=months,
        audit_logs=audit_logs,
    )


def get_month_grid_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    entries: EntryRepository = Depends(get_entry_repository),
    months: MonthRepository = Depends(get_month_repository),
) -> GetMonthGridUseCase:
    return GetMonthGridUseCase(
        users=users, projects=projects, entries=entries, months=months
    )


def get_clear_entry_use_case(
    users: UserRepository = Depends(get_user_repository),
    entries: EntryRepository = Depends(get_entry_repository),
    months: MonthRepository = Depends(get_month_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> ClearEntryUseCase:
    return ClearEntryUseCase(
        users=users, entries=entries, months=months, audit_logs=audit_logs
    )


def get_remove_mission_use_case(
    users: UserRepository = Depends(get_user_repository),
    entries: EntryRepository = Depends(get_entry_repository),
    months: MonthRepository = Depends(get_month_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> RemoveMissionFromMonthUseCase:
    return RemoveMissionFromMonthUseCase(
        users=users, entries=entries, months=months, audit_logs=audit_logs
    )
