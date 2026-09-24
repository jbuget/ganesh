"""Wiring of the entry use cases."""

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db

# The one thing this module needs of the keys: reading the public half of a
# token off the header. Importing the api_keys *presentation* would close a
# circle — that module already comes here for its repositories.
from src.modules.api_keys.domain.services import key_material
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.audit_logs.infrastructure.database.repositories.audit_log_repository_impl import (
    SqlAuditLogRepository,
)
from src.modules.audit_logs.infrastructure.machine_stamped_repository import (
    MachineStampedAuditLog,
)
from src.modules.entries.application.use_cases.add_mission_to_month import (
    AddMissionToMonthUseCase,
)
from src.modules.entries.application.use_cases.clear_entry import ClearEntryUseCase
from src.modules.entries.application.use_cases.export_entries import (
    ExportEntriesUseCase,
)
from src.modules.entries.application.use_cases.get_month_grid import GetMonthGridUseCase
from src.modules.entries.application.use_cases.remove_mission_from_month import (
    RemoveMissionFromMonthUseCase,
)
from src.modules.entries.application.use_cases.set_entry import SetEntryUseCase
from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.entries.domain.repositories.user_mission_repository import (
    UserMissionRepository,
)
from src.modules.entries.infrastructure.database.repositories.entry_repository_impl import (
    SqlEntryRepository,
)
from src.modules.entries.infrastructure.database.repositories.user_mission_repository_impl import (
    SqlUserMissionRepository,
)
from src.modules.months.domain.repositories.month_repository import MonthRepository
from src.modules.months.infrastructure.database.repositories.month_repository_impl import (
    SqlMonthRepository,
)
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.notifications.presentation.dependencies import (
    get_notification_delivery,
)
from src.modules.projects.domain.repositories.activity_repository import (
    ActivityRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.infrastructure.database.repositories.activity_repository_impl import (
    SqlActivityRepository,
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


def get_activity_repository(
    session: AsyncSession = Depends(get_db),
) -> ActivityRepository:
    return SqlActivityRepository(session)


def get_entry_repository(session: AsyncSession = Depends(get_db)) -> EntryRepository:
    return SqlEntryRepository(session)


def get_month_repository(session: AsyncSession = Depends(get_db)) -> MonthRepository:
    return SqlMonthRepository(session)


def get_user_mission_repository(
    session: AsyncSession = Depends(get_db),
) -> UserMissionRepository:
    return SqlUserMissionRepository(session)


def get_audit_log_repository(
    session: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> AuditLogRepository:
    """The log — and, when a machine is calling, the key its lines must name.

    The key is read from the public half of the token alone: no lookup, no
    hash, no authentication. None is needed, and that is the point. A line is
    only ever written on a route that opened its own machine door and checked
    the key there; a forged token would not have reached this far. What gets
    stamped is a lookup handle, which is not a secret and is exactly what the
    table of keys already shows.
    """
    logs: AuditLogRepository = SqlAuditLogRepository(session)
    token = (authorization or "").removeprefix("Bearer ").removeprefix("bearer ")
    if not key_material.looks_like_ours(token):
        return logs
    parsed = key_material.parse(token)
    if parsed is None:
        return logs
    public_id, _ = parsed
    return MachineStampedAuditLog(logs, key_material.masked(public_id))


def get_set_entry_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    activities: ActivityRepository = Depends(get_activity_repository),
    entries: EntryRepository = Depends(get_entry_repository),
    months: MonthRepository = Depends(get_month_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
    notifications: NotificationDelivery = Depends(get_notification_delivery),
) -> SetEntryUseCase:
    return SetEntryUseCase(
        users=users,
        projects=projects,
        activities=activities,
        entries=entries,
        months=months,
        audit_logs=audit_logs,
        notifications=notifications,
    )


def get_month_grid_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    activities: ActivityRepository = Depends(get_activity_repository),
    entries: EntryRepository = Depends(get_entry_repository),
    months: MonthRepository = Depends(get_month_repository),
    user_missions: UserMissionRepository = Depends(get_user_mission_repository),
) -> GetMonthGridUseCase:
    return GetMonthGridUseCase(
        users=users,
        projects=projects,
        activities=activities,
        entries=entries,
        months=months,
        user_missions=user_missions,
    )


def get_add_mission_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    months: MonthRepository = Depends(get_month_repository),
    user_missions: UserMissionRepository = Depends(get_user_mission_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
    notifications: NotificationDelivery = Depends(get_notification_delivery),
) -> AddMissionToMonthUseCase:
    return AddMissionToMonthUseCase(
        users=users,
        projects=projects,
        months=months,
        user_missions=user_missions,
        audit_logs=audit_logs,
        notifications=notifications,
    )


def get_clear_entry_use_case(
    users: UserRepository = Depends(get_user_repository),
    entries: EntryRepository = Depends(get_entry_repository),
    months: MonthRepository = Depends(get_month_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
    notifications: NotificationDelivery = Depends(get_notification_delivery),
) -> ClearEntryUseCase:
    return ClearEntryUseCase(
        users=users,
        entries=entries,
        months=months,
        audit_logs=audit_logs,
        notifications=notifications,
    )


def get_remove_mission_use_case(
    users: UserRepository = Depends(get_user_repository),
    entries: EntryRepository = Depends(get_entry_repository),
    months: MonthRepository = Depends(get_month_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
    user_missions: UserMissionRepository = Depends(get_user_mission_repository),
    notifications: NotificationDelivery = Depends(get_notification_delivery),
) -> RemoveMissionFromMonthUseCase:
    return RemoveMissionFromMonthUseCase(
        users=users,
        entries=entries,
        months=months,
        audit_logs=audit_logs,
        user_missions=user_missions,
        notifications=notifications,
    )


def get_export_entries_use_case(
    entries: EntryRepository = Depends(get_entry_repository),
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
) -> ExportEntriesUseCase:
    return ExportEntriesUseCase(entries=entries, users=users, projects=projects)
