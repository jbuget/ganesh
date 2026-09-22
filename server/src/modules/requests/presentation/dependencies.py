"""Wiring of the request use cases."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.audit_logs.infrastructure.database.repositories.audit_log_repository_impl import (
    SqlAuditLogRepository,
)
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.notifications.infrastructure.database.repositories.notification_repository_impl import (
    SqlNotificationRepository,
)
from src.modules.projects.domain.repositories.project_detail_repository import (
    ProjectDetailRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_detail_repository_impl import (
    SqlProjectDetailRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_repository_impl import (
    SqlProjectRepository,
)
from src.modules.requests.application.use_cases.convert_request import (
    ConvertRequestUseCase,
)
from src.modules.requests.application.use_cases.decide_request import (
    DecideRequestUseCase,
)
from src.modules.requests.application.use_cases.delete_request import (
    DeleteRequestUseCase,
)
from src.modules.requests.application.use_cases.file_request import FileRequestUseCase
from src.modules.requests.application.use_cases.fill_in_request import (
    FillInRequestUseCase,
)
from src.modules.requests.application.use_cases.read_requests import (
    GetRequestUseCase,
    ListMyRequestsUseCase,
    ListRequestsUseCase,
    ListSponsorsUseCase,
)
from src.modules.requests.application.use_cases.submit_request import (
    SubmitRequestUseCase,
)
from src.modules.requests.application.use_cases.withdraw_request import (
    WithdrawRequestUseCase,
)
from src.modules.requests.domain.repositories.request_repository import (
    RequestRepository,
)
from src.modules.requests.infrastructure.database.repositories.request_repository_impl import (
    SqlRequestRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)


def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return SqlUserRepository(session)


def get_request_repository(
    session: AsyncSession = Depends(get_db),
) -> RequestRepository:
    return SqlRequestRepository(session)


def get_audit_log_repository(
    session: AsyncSession = Depends(get_db),
) -> AuditLogRepository:
    return SqlAuditLogRepository(session)


def get_notification_delivery(
    session: AsyncSession = Depends(get_db),
) -> NotificationDelivery:
    return NotificationDelivery(SqlNotificationRepository(session))


def get_file_request_use_case(
    users: UserRepository = Depends(get_user_repository),
    requests: RequestRepository = Depends(get_request_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> FileRequestUseCase:
    return FileRequestUseCase(users=users, requests=requests, audit_logs=audit_logs)


def get_fill_in_request_use_case(
    users: UserRepository = Depends(get_user_repository),
    requests: RequestRepository = Depends(get_request_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> FillInRequestUseCase:
    return FillInRequestUseCase(users=users, requests=requests, audit_logs=audit_logs)


def get_submit_request_use_case(
    users: UserRepository = Depends(get_user_repository),
    requests: RequestRepository = Depends(get_request_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
    notifications: NotificationDelivery = Depends(get_notification_delivery),
) -> SubmitRequestUseCase:
    return SubmitRequestUseCase(
        users=users,
        requests=requests,
        audit_logs=audit_logs,
        notifications=notifications,
    )


def get_withdraw_request_use_case(
    users: UserRepository = Depends(get_user_repository),
    requests: RequestRepository = Depends(get_request_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> WithdrawRequestUseCase:
    return WithdrawRequestUseCase(users=users, requests=requests, audit_logs=audit_logs)


def get_delete_request_use_case(
    requests: RequestRepository = Depends(get_request_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> DeleteRequestUseCase:
    return DeleteRequestUseCase(requests=requests, audit_logs=audit_logs)


def get_request_use_case(
    users: UserRepository = Depends(get_user_repository),
    requests: RequestRepository = Depends(get_request_repository),
) -> GetRequestUseCase:
    return GetRequestUseCase(users=users, requests=requests)


def get_my_requests_use_case(
    users: UserRepository = Depends(get_user_repository),
    requests: RequestRepository = Depends(get_request_repository),
) -> ListMyRequestsUseCase:
    return ListMyRequestsUseCase(users=users, requests=requests)


def get_sponsors_use_case(
    users: UserRepository = Depends(get_user_repository),
) -> ListSponsorsUseCase:
    return ListSponsorsUseCase(users=users)


def get_decide_request_use_case(
    users: UserRepository = Depends(get_user_repository),
    requests: RequestRepository = Depends(get_request_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> DecideRequestUseCase:
    return DecideRequestUseCase(users=users, requests=requests, audit_logs=audit_logs)


def get_requests_use_case(
    users: UserRepository = Depends(get_user_repository),
    requests: RequestRepository = Depends(get_request_repository),
) -> ListRequestsUseCase:
    return ListRequestsUseCase(users=users, requests=requests)


def get_project_repository(
    session: AsyncSession = Depends(get_db),
) -> ProjectRepository:
    return SqlProjectRepository(session)


def get_project_detail_repository(
    session: AsyncSession = Depends(get_db),
) -> ProjectDetailRepository:
    return SqlProjectDetailRepository(session)


def get_convert_request_use_case(
    users: UserRepository = Depends(get_user_repository),
    requests: RequestRepository = Depends(get_request_repository),
    projects: ProjectRepository = Depends(get_project_repository),
    details: ProjectDetailRepository = Depends(get_project_detail_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> ConvertRequestUseCase:
    return ConvertRequestUseCase(
        users=users,
        requests=requests,
        projects=projects,
        details=details,
        audit_logs=audit_logs,
    )
