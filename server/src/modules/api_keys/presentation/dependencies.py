"""Wiring the service-account use cases, and the door a machine comes in by.

`require_scope` lives here rather than beside `get_current_user`: what it
admits is a key, and putting it in the auth module made that module drag the
whole of this one — application, infrastructure and all — behind it. Auth now
knows one thing of the keys, the prefix that tells one at the door.
"""

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from datetime import timedelta
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
from src.modules.api_keys.domain.entities.api_key import ApiKey, ApiKeyScope
from src.modules.api_keys.domain.repositories.api_key_repository import ApiKeyRepository
from src.modules.api_keys.domain.repositories.rate_limit_store import RateLimitStore
from src.modules.api_keys.domain.services import key_material
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
from src.modules.auth.presentation.dependencies import admit, get_signed_in_user

# Declared once, in the entries module, and imported from there by projects and
# users alike: one provider per repository, whatever module asks for it.
from src.modules.entries.presentation.dependencies import (
    get_audit_log_repository,
    get_user_repository,
)
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.notifications.presentation.dependencies import (
    get_notification_delivery,
)
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.utils import clock


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
    notifications: NotificationDelivery = Depends(get_notification_delivery),
) -> CreateApiKeyUseCase:
    return CreateApiKeyUseCase(
        keys=keys, users=users, audit_logs=audit_logs, notifications=notifications
    )


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
    notifications: NotificationDelivery = Depends(get_notification_delivery),
) -> RevokeApiKeyUseCase:
    return RevokeApiKeyUseCase(
        keys=keys, audit_logs=audit_logs, notifications=notifications
    )


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


#: Every scope some route asks for, filled as the doors are built — which
#: happens once, at import time, when the routers are read.
#:
#: It exists for one test. A scope the form offers and no route opens is a
#: table of keys that says what a key opens and says it wrong, and that is the
#: fault this second round of scopes was written to remove.
OPENED_SCOPES: set[ApiKeyScope] = set()


@dataclass(frozen=True)
class Caller:
    """Who is at the other end of a route the team and a machine both reach.

    A teammate who signed in, or a machine and the human who answers for it.
    Either way what comes out is an `actor_id`, which is all a use case has
    ever been handed: the audit records the owner, and the key is named beside
    it in the payload.
    """

    actor_id: int
    #: The key that called, when a machine did. `None` for a teammate.
    key: ApiKey | None = None

    @property
    def is_machine(self) -> bool:
        return self.key is not None


def bearer_token(authorization: str | None) -> str | None:
    """The token carried by an `Authorization: Bearer …` header, if any."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    return authorization.split(" ", 1)[1]


async def admit_machine(
    scope: ApiKeyScope,
    authorization: str | None,
    response: Response,
    use_case: AuthenticateApiKeyUseCase,
    rate_limit: CheckRateLimitUseCase,
    session: AsyncSession,
) -> MachineCaller:
    """Checks a key at the door, for one scope.

    Unknown, malformed, expired, revoked, owner deactivated: all five answer
    `401`, and none of them says which. Telling an expired key from an unknown
    one hands an attacker a way to enumerate. A valid key without the scope
    answers `403`, because there the caller needs to know what to ask for.

    A key that has called too often answers `429`, and every answer — that one
    included — carries what is left of the allowance. A caller should be able
    to slow down before being told to.
    """
    token = bearer_token(authorization)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    caller = await use_case.execute(token, scope)
    if caller is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Consulted once the key has proved itself: the limit guards against a
    # caller that holds a real key, not against noise at the door.
    assert caller.key.id is not None
    decision = await rate_limit.execute(caller.key.id, clock.now())
    announce(response, rate_limit.allowance, decision)
    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many calls for this API key.",
            headers=rate_headers(rate_limit.allowance, decision),
        )

    # `last_used_at` is written through a freshness window, so this commits at
    # most once every quarter of an hour per key.
    await session.commit()
    return caller


def require_scope(
    scope: ApiKeyScope,
) -> Callable[..., Coroutine[Any, Any, MachineCaller]]:
    """Opens one route to a machine, **and to nobody else**.

    A key opens nothing by default. A route becomes machine-reachable by
    asking for it here, explicitly, one route at a time — which is why adding
    a key to Ganesh changes the reach of no existing route.

    This is the door for a route the team has no business on: the catalogue
    export, which exists for waat.tools to read. A route the team already uses
    takes `open_to_machines` instead, which adds a door rather than swapping
    one for another.
    """

    OPENED_SCOPES.add(scope)

    async def dependency(
        response: Response,
        authorization: str | None = Header(default=None),
        use_case: AuthenticateApiKeyUseCase = Depends(
            get_authenticate_api_key_use_case
        ),
        rate_limit: CheckRateLimitUseCase = Depends(get_check_rate_limit_use_case),
        session: AsyncSession = Depends(get_db),
    ) -> MachineCaller:
        return await admit_machine(
            scope, authorization, response, use_case, rate_limit, session
        )

    return dependency


async def teammate_or_machine(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User | None:
    """The teammate at the door, or `None` when it is a machine standing there.

    The `jns_` prefix is what tells them apart — the same reading
    `get_current_user` does to turn a key away. A teammate's token never
    touches the key path, and a key never touches the Entra path.

    The door is **called** rather than declared. FastAPI resolves every
    declared dependency, so a key would be refused by the human door before
    the machine one was ever consulted. This wrapper is the seam that survives
    that: it is a dependency in its own right, so a test stands a teammate at
    the door without having to stand down the whole door.

    Called in two steps, exactly as `get_current_user` declares them: whoever
    signed in is resolved, then admitted — a guest is turned away here as
    everywhere else, and a route open to machines stays the team's.
    """
    token = bearer_token(authorization)
    if token is not None and key_material.looks_like_ours(token):
        return None
    return admit(await get_signed_in_user(authorization, session, settings))


def open_to_machines(
    scope: ApiKeyScope,
) -> Callable[..., Coroutine[Any, Any, Caller]]:
    """Adds a machine door to a route the team already comes through.

    Unlike `require_scope`, this takes nothing away: whoever signed in keeps
    coming in exactly as before, and a key gains a way in beside them.

    What a route gets back is a `Caller`, so a write records an actor whoever
    called — the teammate, or the human who answers for the machine. A read
    ignores it, as it already ignored the user.
    """

    OPENED_SCOPES.add(scope)

    async def dependency(
        response: Response,
        teammate: User | None = Depends(teammate_or_machine),
        authorization: str | None = Header(default=None),
        use_case: AuthenticateApiKeyUseCase = Depends(
            get_authenticate_api_key_use_case
        ),
        rate_limit: CheckRateLimitUseCase = Depends(get_check_rate_limit_use_case),
        session: AsyncSession = Depends(get_db),
    ) -> Caller:
        if teammate is not None:
            assert teammate.id is not None
            # A scope says its verb, and a write scope admits nobody who may
            # not write. A guest comes in through every reading door beside
            # this one, and is turned back here — the same refusal
            # `get_contributor` gives on a route no machine reaches.
            if not scope.is_read and not teammate.can_write():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This account may read Ganesh, not write into it.",
                )
            return Caller(actor_id=teammate.id)

        machine = await admit_machine(
            scope, authorization, response, use_case, rate_limit, session
        )
        return Caller(actor_id=machine.actor_id, key=machine.key)

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
