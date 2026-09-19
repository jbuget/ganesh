"""Wiring the service-account use cases."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.api_keys.application.use_cases.authenticate_api_key import (
    AuthenticateApiKeyUseCase,
)
from src.modules.api_keys.application.use_cases.manage_api_keys import (
    CreateApiKeyUseCase,
    ListApiKeysUseCase,
    RevokeApiKeyUseCase,
    UpdateApiKeyUseCase,
)
from src.modules.api_keys.domain.repositories.api_key_repository import ApiKeyRepository
from src.modules.api_keys.infrastructure.database.repositories.api_key_repository_impl import (
    SqlApiKeyRepository,
)
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.audit_logs.infrastructure.database.repositories.audit_log_repository_impl import (
    SqlAuditLogRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)


def get_api_key_repository(
    session: AsyncSession = Depends(get_db),
) -> ApiKeyRepository:
    return SqlApiKeyRepository(session)


def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return SqlUserRepository(session)


def get_audit_log_repository(
    session: AsyncSession = Depends(get_db),
) -> AuditLogRepository:
    return SqlAuditLogRepository(session)


def get_authenticate_api_key_use_case(
    keys: ApiKeyRepository = Depends(get_api_key_repository),
    users: UserRepository = Depends(get_user_repository),
) -> AuthenticateApiKeyUseCase:
    """The seam `require_scope` hangs on, so a test can stand in for it."""
    return AuthenticateApiKeyUseCase(keys=keys, users=users)


def get_create_api_key_use_case(
    keys: ApiKeyRepository = Depends(get_api_key_repository),
    users: UserRepository = Depends(get_user_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> CreateApiKeyUseCase:
    return CreateApiKeyUseCase(keys=keys, users=users, audit_logs=audit_logs)


def get_list_api_keys_use_case(
    keys: ApiKeyRepository = Depends(get_api_key_repository),
    users: UserRepository = Depends(get_user_repository),
) -> ListApiKeysUseCase:
    return ListApiKeysUseCase(keys=keys, users=users)


def get_update_api_key_use_case(
    keys: ApiKeyRepository = Depends(get_api_key_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> UpdateApiKeyUseCase:
    return UpdateApiKeyUseCase(keys=keys, audit_logs=audit_logs)


def get_revoke_api_key_use_case(
    keys: ApiKeyRepository = Depends(get_api_key_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> RevokeApiKeyUseCase:
    return RevokeApiKeyUseCase(keys=keys, audit_logs=audit_logs)
