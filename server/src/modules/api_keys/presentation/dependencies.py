"""Wiring the service-account use cases, and the door a machine comes in by.

`require_scope` lives here rather than beside `get_current_user`: what it
admits is a key, and putting it in the auth module made that module drag the
whole of this one — application, infrastructure and all — behind it. Auth now
knows one thing of the keys, the prefix that tells one at the door.
"""

from collections.abc import Callable, Coroutine
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any

from fastapi import Depends, Header, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.database import get_db
from src.modules.api_keys.application.use_cases.authenticate_api_key import (
    AuthenticateApiKeyUseCase,
    MachineCaller,
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
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.api_keys.domain.repositories.api_key_repository import ApiKeyRepository
from src.modules.api_keys.domain.repositories.rate_limit_store import RateLimitStore
from src.modules.api_keys.domain.services.rate_limit import Decision, RateLimit
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


def require_scope(
    scope: ApiKeyScope,
) -> Callable[..., Coroutine[Any, Any, MachineCaller]]:
    """Opens one route to a machine carrying one scope.

    A key opens nothing by default. A route becomes machine-reachable by
    asking for it here, explicitly, one route at a time — which is why adding
    a key to Ganesh changes the reach of no existing route.

    Unknown, malformed, expired, revoked, owner deactivated: all five answer
    `401`, and none of them says which. Telling an expired key from an unknown
    one hands an attacker a way to enumerate. A valid key without the scope
    answers `403`, because there the caller needs to know what to ask for.

    A key that has called too often answers `429`, and every answer — that one
    included — carries what is left of the allowance. A caller should be able
    to slow down before being told to.
    """

    async def dependency(
        response: Response,
        authorization: str | None = Header(default=None),
        use_case: AuthenticateApiKeyUseCase = Depends(
            get_authenticate_api_key_use_case
        ),
        rate_limit: CheckRateLimitUseCase = Depends(get_check_rate_limit_use_case),
        session: AsyncSession = Depends(get_db),
    ) -> MachineCaller:
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing API key.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        caller = await use_case.execute(authorization.split(" ", 1)[1], scope)
        if caller is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Consulted once the key has proved itself: the limit guards against a
        # caller that holds a real key, not against noise at the door.
        assert caller.key.id is not None
        decision = await rate_limit.execute(caller.key.id, datetime.now())
        announce(response, rate_limit.allowance, decision)
        if not decision.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many calls for this API key.",
                headers=rate_headers(rate_limit.allowance, decision),
            )

        # `last_used_at` is written through a freshness window, so this commits
        # at most once every quarter of an hour per key.
        await session.commit()
        return caller

    return dependency


def rate_headers(allowance: int, decision: Decision) -> dict[str, str]:
    """What every answer says about the allowance.

    `X-RateLimit-*` rather than the `RateLimit-*` of the draft RFC: the former
    is what clients and libraries actually look for today. `Retry-After` rides
    along when the door is shut, because it is the one a client obeys without
    being taught anything.
    """
    headers = {
        "X-RateLimit-Limit": str(allowance),
        "X-RateLimit-Remaining": str(decision.remaining),
    }
    if not decision.allowed:
        headers["Retry-After"] = str(decision.retry_after_seconds)
    return headers


def announce(response: Response, allowance: int, decision: Decision) -> None:
    """Carries the allowance on the way out, refusal or not."""
    response.headers.update(rate_headers(allowance, decision))
