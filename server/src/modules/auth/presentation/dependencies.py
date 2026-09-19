"""Authenticating requests and resolving the current user."""

import logging
from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.database import get_db
from src.modules.api_keys.application.use_cases.authenticate_api_key import (
    AuthenticateApiKeyUseCase,
    MachineCaller,
)
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.api_keys.domain.services import key_material
from src.modules.api_keys.presentation.dependencies import (
    get_authenticate_api_key_use_case,
)
from src.modules.auth.infrastructure.entra_token_validator import EntraTokenValidator
from src.modules.auth.presentation.identity import identity_from_claims
from src.modules.users.application.dtos.user_dto import EntraIdentity
from src.modules.users.application.use_cases.provision_user import ProvisionUserUseCase
from src.modules.users.domain.entities.user import User
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)
from src.shared.exceptions.domain_exceptions import ForbiddenActionError

logger = logging.getLogger(__name__)

#: Identity used when authentication is switched off in development.
DEV_IDENTITY = EntraIdentity(
    oid="dev-local",
    email="j.buget@waat.fr",
    display_name="J. Buget (dev)",
)


async def get_current_user(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    """Resolves the current user, provisioning them if need be.

    With `REQUIRE_AUTH=false`, a development identity is used: it allows work
    without having declared the redirect URI on the Entra side. This mode must
    never be active in production.
    """
    # An API key is not a person. Every route that leans on this dependency is
    # human-only, and stays so: a machine reaches a route by that route asking
    # for a scope, never by turning up with a key on a human door.
    if authorization and key_material.looks_like_ours(
        authorization.removeprefix("Bearer ").removeprefix("bearer ")
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="An API key cannot be used on this route.",
        )

    provision = ProvisionUserUseCase(users=SqlUserRepository(session))

    if not settings.require_auth:
        logger.warning("Authentication disabled: development identity.")
        user = await provision.execute(DEV_IDENTITY)
        await session.commit()
        return user

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    validator = EntraTokenValidator(
        tenant_id=settings.azure_ad_tenant_id,
        client_id=settings.azure_ad_client_id,
    )
    try:
        claims = await validator.validate(authorization.split(" ", 1)[1])
        identity = identity_from_claims(claims)
    except ForbiddenActionError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    user = await provision.execute(identity)
    await session.commit()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is deactivated.",
        )
    return user


async def get_current_manager(
    user: User = Depends(get_current_user),
) -> User:
    """Restricts access to managers."""
    if not user.can_manage_teammates():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action is reserved for managers.",
        )
    return user


def require_scope(
    scope: ApiKeyScope,
) -> Callable[..., Coroutine[Any, Any, MachineCaller]]:
    """Opens one route to a machine carrying one scope.

    A key opens nothing by default. A route becomes machine-reachable by
    asking for it here, explicitly, one route at a time — which is why adding
    a key to Janus changes the reach of no existing route.

    Unknown, malformed, expired, revoked, owner deactivated: all five answer
    `401`, and none of them says which. Telling an expired key from an unknown
    one hands an attacker a way to enumerate. A valid key without the scope
    answers `403`, because there the caller needs to know what to ask for.
    """

    async def dependency(
        authorization: str | None = Header(default=None),
        use_case: AuthenticateApiKeyUseCase = Depends(
            get_authenticate_api_key_use_case
        ),
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

        # `last_used_at` is written through a freshness window, so this commits
        # at most once every quarter of an hour per key.
        await session.commit()
        return caller

    return dependency
