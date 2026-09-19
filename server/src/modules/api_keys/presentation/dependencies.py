"""Wiring the service-account use cases."""

from datetime import timedelta
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.database import get_db
from src.modules.api_keys.application.use_cases.authenticate_api_key import (
    AuthenticateApiKeyUseCase,
)
from src.modules.api_keys.application.use_cases.check_rate_limit import (
    CheckRateLimitUseCase,
)
from src.modules.api_keys.application.use_cases.manage_api_keys import (
    CreateApiKeyUseCase,
    ListApiKeysUseCase,
    RevokeApiKeyUseCase,
    UpdateApiKeyUseCase,
)
from src.modules.api_keys.domain.repositories.api_key_repository import ApiKeyRepository
from src.modules.api_keys.domain.repositories.rate_limit_store import RateLimitStore
from src.modules.api_keys.domain.services.rate_limit import RateLimit
from src.modules.api_keys.infrastructure.database.repositories.api_key_repository_impl import (
    SqlApiKeyRepository,
)
from src.modules.api_keys.infrastructure.rate_limit.in_memory_rate_limit_store import (
    InMemoryRateLimitStore,
)
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)

# Declared once, in the entries module, and imported from there by projects and
# users alike: one provider per repository, whatever module asks for it.
from src.modules.entries.presentation.dependencies import (
    get_audit_log_repository,
    get_user_repository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository


def get_api_key_repository(
    session: AsyncSession = Depends(get_db),
) -> ApiKeyRepository:
    return SqlApiKeyRepository(session)


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
    users: UserRepository = Depends(get_user_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> UpdateApiKeyUseCase:
    return UpdateApiKeyUseCase(keys=keys, users=users, audit_logs=audit_logs)


def get_revoke_api_key_use_case(
    keys: ApiKeyRepository = Depends(get_api_key_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> RevokeApiKeyUseCase:
    return RevokeApiKeyUseCase(keys=keys, audit_logs=audit_logs)


@lru_cache
def get_rate_limit_store() -> RateLimitStore:
    """One store for the whole process.

    Cached, not built per request: buckets that were forgotten between two
    calls would limit nothing at all.
    """
    return InMemoryRateLimitStore()


def get_check_rate_limit_use_case(
    store: RateLimitStore = Depends(get_rate_limit_store),
    settings: Settings = Depends(get_settings),
) -> CheckRateLimitUseCase:
    return CheckRateLimitUseCase(
        store=store,
        limit=RateLimit(
            allowance=settings.api_key_rate_allowance,
            window=timedelta(seconds=settings.api_key_rate_window_seconds),
        ),
    )
