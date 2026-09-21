"""Wiring of the reference list use cases."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
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
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.notifications.presentation.dependencies import (
    get_notification_delivery,
)
from src.modules.projects.application.use_cases.archive_project import (
    ArchiveProjectUseCase,
    UnarchiveProjectUseCase,
)
from src.modules.projects.application.use_cases.assign_member import (
    AssignMemberUseCase,
    UnassignMemberUseCase,
)
from src.modules.projects.application.use_cases.attach_project import (
    AttachProjectUseCase,
    DetachProjectUseCase,
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
from src.modules.projects.application.use_cases.export_catalog import (
    ExportCatalogUseCase,
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
from src.modules.projects.application.use_cases.project_attachments import (
    DownloadProjectAttachmentUseCase,
    ListProjectAttachmentsUseCase,
    RemoveProjectAttachmentUseCase,
    UploadProjectAttachmentUseCase,
)
from src.modules.projects.application.use_cases.project_updates import (
    EditProjectUpdateUseCase,
    ListProjectUpdatesUseCase,
    PostProjectUpdateUseCase,
    RemoveProjectUpdateUseCase,
)
from src.modules.projects.application.use_cases.update_project import (
    UpdateProjectUseCase,
)
from src.modules.projects.application.use_cases.update_project_detail import (
    AddProjectLinkUseCase,
    RemoveProjectLinkUseCase,
    UpdateDescriptionUseCase,
    UpdateProjectDetailUseCase,
)
from src.modules.projects.application.use_cases.update_project_registry import (
    UpdateProjectRegistryUseCase,
)
from src.modules.projects.domain.repositories.attachment_store import AttachmentStore
from src.modules.projects.domain.repositories.project_assignee_repository import (
    ProjectAssigneeRepository,
)
from src.modules.projects.domain.repositories.project_attachment_repository import (
    ProjectAttachmentRepository,
)
from src.modules.projects.domain.repositories.project_detail_repository import (
    ProjectDetailRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.repositories.project_update_repository import (
    ProjectUpdateRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_assignee_repository_impl import (
    SqlProjectAssigneeRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_attachment_repository_impl import (
    SqlProjectAttachmentRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_detail_repository_impl import (
    SqlProjectDetailRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_update_repository_impl import (
    SqlProjectUpdateRepository,
)
from src.modules.projects.infrastructure.storage.s3_attachment_store import (
    S3AttachmentStore,
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


def get_project_update_repository(
    session: AsyncSession = Depends(get_db),
) -> ProjectUpdateRepository:
    return SqlProjectUpdateRepository(session)


def get_project_attachment_repository(
    session: AsyncSession = Depends(get_db),
) -> ProjectAttachmentRepository:
    return SqlProjectAttachmentRepository(session)


def get_attachment_store(
    settings: Settings = Depends(get_settings),
) -> AttachmentStore:
    """The bucket the files sit in — S3 in production, MinIO on a laptop."""
    return S3AttachmentStore(
        bucket=settings.s3_bucket,
        region=settings.s3_region,
        endpoint_url=settings.s3_endpoint_url,
        access_key_id=settings.s3_access_key_id,
        secret_access_key=settings.s3_secret_access_key,
    )


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
    assignees: ProjectAssigneeRepository = Depends(get_project_assignee_repository),
    notifications: NotificationDelivery = Depends(get_notification_delivery),
) -> ChangeProjectStatusUseCase:
    return ChangeProjectStatusUseCase(
        users=users,
        projects=projects,
        details=details,
        audit_logs=audit_logs,
        assignees=assignees,
        notifications=notifications,
    )


def get_list_projects_use_case(
    projects: ProjectRepository = Depends(get_project_repository),
    entries: EntryRepository = Depends(get_entry_repository),
    assignees: ProjectAssigneeRepository = Depends(get_project_assignee_repository),
    users: UserRepository = Depends(get_user_repository),
    updates: ProjectUpdateRepository = Depends(get_project_update_repository),
    details: ProjectDetailRepository = Depends(get_project_detail_repository),
) -> ListProjectsUseCase:
    return ListProjectsUseCase(
        projects=projects,
        entries=entries,
        assignees=assignees,
        users=users,
        updates=updates,
        details=details,
    )


def get_delete_project_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    entries: EntryRepository = Depends(get_entry_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
    assignees: ProjectAssigneeRepository = Depends(get_project_assignee_repository),
    notifications: NotificationDelivery = Depends(get_notification_delivery),
    attachments: ProjectAttachmentRepository = Depends(
        get_project_attachment_repository
    ),
    store: AttachmentStore = Depends(get_attachment_store),
) -> DeleteProjectUseCase:
    return DeleteProjectUseCase(
        users=users,
        projects=projects,
        entries=entries,
        audit_logs=audit_logs,
        assignees=assignees,
        notifications=notifications,
        attachments=attachments,
        store=store,
    )


def get_attach_project_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> AttachProjectUseCase:
    return AttachProjectUseCase(users=users, projects=projects, audit_logs=audit_logs)


def get_detach_project_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> DetachProjectUseCase:
    return DetachProjectUseCase(users=users, projects=projects, audit_logs=audit_logs)


def get_archive_project_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
    assignees: ProjectAssigneeRepository = Depends(get_project_assignee_repository),
    notifications: NotificationDelivery = Depends(get_notification_delivery),
) -> ArchiveProjectUseCase:
    return ArchiveProjectUseCase(
        users=users,
        projects=projects,
        audit_logs=audit_logs,
        assignees=assignees,
        notifications=notifications,
    )


def get_unarchive_project_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> UnarchiveProjectUseCase:
    return UnarchiveProjectUseCase(
        users=users, projects=projects, audit_logs=audit_logs
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
    updates: ProjectUpdateRepository = Depends(get_project_update_repository),
    details: ProjectDetailRepository = Depends(get_project_detail_repository),
) -> GetBoardUseCase:
    return GetBoardUseCase(
        projects=projects,
        entries=entries,
        users=users,
        assignees=assignees,
        updates=updates,
        details=details,
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
    notifications: NotificationDelivery = Depends(get_notification_delivery),
) -> AssignMemberUseCase:
    return AssignMemberUseCase(
        users=users,
        projects=projects,
        assignees=assignees,
        audit_logs=audit_logs,
        notifications=notifications,
    )


def get_unassign_member_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    assignees: ProjectAssigneeRepository = Depends(get_project_assignee_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
    notifications: NotificationDelivery = Depends(get_notification_delivery),
) -> UnassignMemberUseCase:
    return UnassignMemberUseCase(
        users=users,
        projects=projects,
        assignees=assignees,
        audit_logs=audit_logs,
        notifications=notifications,
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


def get_export_catalog_use_case(
    projects: ProjectRepository = Depends(get_project_repository),
    details: ProjectDetailRepository = Depends(get_project_detail_repository),
    assignees: ProjectAssigneeRepository = Depends(get_project_assignee_repository),
    users: UserRepository = Depends(get_user_repository),
) -> ExportCatalogUseCase:
    return ExportCatalogUseCase(
        projects=projects, details=details, assignees=assignees, users=users
    )


def get_update_project_registry_use_case(
    projects: ProjectRepository = Depends(get_project_repository),
    details: ProjectDetailRepository = Depends(get_project_detail_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> UpdateProjectRegistryUseCase:
    return UpdateProjectRegistryUseCase(
        projects=projects, details=details, audit_logs=audit_logs
    )


def get_add_project_link_use_case(
    projects: ProjectRepository = Depends(get_project_repository),
    details: ProjectDetailRepository = Depends(get_project_detail_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> AddProjectLinkUseCase:
    return AddProjectLinkUseCase(
        projects=projects, details=details, audit_logs=audit_logs
    )


def get_remove_project_link_use_case(
    details: ProjectDetailRepository = Depends(get_project_detail_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> RemoveProjectLinkUseCase:
    return RemoveProjectLinkUseCase(details=details, audit_logs=audit_logs)


def get_update_description_use_case(
    projects: ProjectRepository = Depends(get_project_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> UpdateDescriptionUseCase:
    return UpdateDescriptionUseCase(projects=projects, audit_logs=audit_logs)


def _thread_write(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    updates: ProjectUpdateRepository = Depends(get_project_update_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
    assignees: ProjectAssigneeRepository = Depends(get_project_assignee_repository),
    notifications: NotificationDelivery = Depends(get_notification_delivery),
) -> dict[str, object]:
    """What the thread writes share."""
    return {
        "users": users,
        "projects": projects,
        "updates": updates,
        "audit_logs": audit_logs,
        "assignees": assignees,
        "notifications": notifications,
    }


def get_post_update_use_case(
    repositories: dict[str, object] = Depends(_thread_write),
) -> PostProjectUpdateUseCase:
    return PostProjectUpdateUseCase(**repositories)  # type: ignore[arg-type]


def get_edit_update_use_case(
    repositories: dict[str, object] = Depends(_thread_write),
) -> EditProjectUpdateUseCase:
    return EditProjectUpdateUseCase(**repositories)  # type: ignore[arg-type]


def get_remove_update_use_case(
    repositories: dict[str, object] = Depends(_thread_write),
) -> RemoveProjectUpdateUseCase:
    return RemoveProjectUpdateUseCase(**repositories)  # type: ignore[arg-type]


def get_list_updates_use_case(
    updates: ProjectUpdateRepository = Depends(get_project_update_repository),
    users: UserRepository = Depends(get_user_repository),
) -> ListProjectUpdatesUseCase:
    return ListProjectUpdatesUseCase(updates=updates, users=users)


def get_upload_attachment_use_case(
    users: UserRepository = Depends(get_user_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    attachments: ProjectAttachmentRepository = Depends(
        get_project_attachment_repository
    ),
    store: AttachmentStore = Depends(get_attachment_store),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> UploadProjectAttachmentUseCase:
    return UploadProjectAttachmentUseCase(
        users=users,
        projects=projects,
        attachments=attachments,
        store=store,
        audit_logs=audit_logs,
    )


def get_remove_attachment_use_case(
    attachments: ProjectAttachmentRepository = Depends(
        get_project_attachment_repository
    ),
    store: AttachmentStore = Depends(get_attachment_store),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> RemoveProjectAttachmentUseCase:
    return RemoveProjectAttachmentUseCase(
        attachments=attachments, store=store, audit_logs=audit_logs
    )


def get_list_attachments_use_case(
    attachments: ProjectAttachmentRepository = Depends(
        get_project_attachment_repository
    ),
    updates: ProjectUpdateRepository = Depends(get_project_update_repository),
    users: UserRepository = Depends(get_user_repository),
) -> ListProjectAttachmentsUseCase:
    return ListProjectAttachmentsUseCase(
        attachments=attachments, updates=updates, users=users
    )


def get_download_attachment_use_case(
    attachments: ProjectAttachmentRepository = Depends(
        get_project_attachment_repository
    ),
    store: AttachmentStore = Depends(get_attachment_store),
) -> DownloadProjectAttachmentUseCase:
    return DownloadProjectAttachmentUseCase(attachments=attachments, store=store)
