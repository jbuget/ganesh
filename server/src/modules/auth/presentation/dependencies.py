"""Authenticating requests and resolving the current user."""

import logging

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.database import get_db

# The one thing this module needs of the keys: recognising one at the door.
# Admitting a machine lives in the api_keys module, beside what it admits.
from src.modules.api_keys.domain.services import key_material
from src.modules.audit_logs.infrastructure.database.repositories.audit_log_repository_impl import (
    SqlAuditLogRepository,
)
from src.modules.auth.application.use_cases.sign_in_locally import (
    ExpectedCredentials,
    SignInLocallyUseCase,
)
from src.modules.auth.infrastructure.entra_token_validator import EntraTokenValidator
from src.modules.auth.infrastructure.local_tokens import LocalTokenService
from src.modules.auth.presentation.identity import identity_from_claims
from src.modules.users.application.dtos.user_dto import EntraIdentity
from src.modules.users.application.use_cases.provision_user import ProvisionUserUseCase
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)
from src.shared.exceptions.domain_exceptions import ForbiddenActionError

logger = logging.getLogger(__name__)


def dev_identity(email: str) -> EntraIdentity:
    """The identity the open door hands over, in development.

    Which account it is comes from `DEV_EMAIL`, so that one signs in as a
    teammate or as a colleague by editing one line and restarting. The account
    comes into being as an administrator, as every account the open door hands
    over does; `make grant-role` is what moves it to another audience.

    The id is drawn from the address rather than fixed. A fixed one would
    match whichever account was provisioned first and quietly hand over
    somebody else's.
    """
    return EntraIdentity(
        oid=f"dev-{email}",
        email=email,
        display_name=f"{email.split('@')[0]} (dev)",
    )


def get_sign_in_locally_use_case(
    settings: Settings = Depends(get_settings),
) -> SignInLocallyUseCase:
    """Wires the fallback door from the environment, and nowhere deeper.

    Whether the door exists at all is read here: `auth_entra` is a setting,
    and a use case that consulted one would be a use case that knows what a
    setting is.
    """
    return SignInLocallyUseCase(
        fallback_is_open=not settings.auth_entra,
        expected=ExpectedCredentials(
            login=settings.auth_login, password=settings.auth_password
        ),
        issuer=local_token_service(settings),
    )


def local_token_service(settings: Settings) -> LocalTokenService:
    """The fallback door, refusing to exist without a key to sign with."""
    if not settings.secret_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SECRET_KEY est absent : la connexion locale ne peut pas signer.",
        )
    return LocalTokenService(
        secret_key=settings.secret_key, email=settings.auth_local_email
    )


def admit(user: User) -> User:
    """The door: who walks into the application, and who is turned away.

    Written apart from the dependency that calls it so that it can be read —
    and tested — for what it is: the one place the application says who it is
    for.
    """
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is deactivated.",
        )
    # A guest is recognised at the door and goes no further: every screen
    # of the application leans on this dependency, and therefore stays the
    # team's. The requests open themselves to them, one route at a time, the
    # way a route opens itself to a machine.
    if user.is_guest:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account may only reach the requests.",
        )
    return user


async def get_signed_in_user(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    """Resolves whoever is signed in, provisioning them if need be.

    Anybody with an Entra identity, guests included — which is why almost no
    route depends on it. What it is for is the handful of routes that a guest
    must reach, and they say so by asking for it.

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

    provision = ProvisionUserUseCase(
        users=SqlUserRepository(session), audit_logs=SqlAuditLogRepository(session)
    )

    if not settings.require_auth:
        logger.warning("Authentication disabled: signed in as %s.", settings.dev_email)
        # An administrator, and only here: with no door there is nobody to
        # promote this account and nobody it could be confused with. A guest
        # would mean a laptop on which nothing can be declared, which is the
        # opposite of what switching authentication off is for. To be the
        # other audience instead, move that account with `make grant-role`.
        user = await provision.execute(
            dev_identity(settings.dev_email), first_role=Role.ADMIN
        )
        await session.commit()
        return user

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1]
    try:
        # Two doors, one shape of claims behind them: what follows never has to
        # know which one was used.
        if settings.auth_entra:
            claims = await EntraTokenValidator(
                tenant_id=settings.azure_ad_tenant_id,
                client_id=settings.azure_ad_client_id,
            ).validate(token)
        else:
            claims = local_token_service(settings).validate(token)
        identity = identity_from_claims(claims)
    except ForbiddenActionError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    user = await provision.execute(identity)
    await session.commit()
    return user


async def get_current_user(
    user: User = Depends(get_signed_in_user),
) -> User:
    """The user every screen of the application is read by: a team member."""
    return admit(user)


async def get_asker(
    user: User = Depends(get_signed_in_user),
) -> User:
    """The one door a guest comes through: the recueil, and nothing else.

    It is to a guest what `get_contributor` is to the team — the door a route
    that writes hangs off, named so that `test_write_doors` can read it. Every
    route of the recueil asks for it, and no other route may: a route that
    wanted a guest to reach it would be a route reopening the application.

    A deactivated account is turned back here as everywhere else. Access cut
    off is access cut off, whichever audience one belongs to.
    """
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is deactivated.",
        )
    return user


async def get_contributor(
    user: User = Depends(get_current_user),
) -> User:
    """Restricts a route to whoever may write into Ganesh.

    A guest never comes this far — `get_current_user` turns them away at the
    door — so what this one holds back is a deactivated account, and it is
    where a rung between guest and teammate would land the day there is one.

    The door is **here** rather than in each use case because there are forty
    of them that write, and one forgotten is somebody writing who may not. A
    mutating route
    hangs off this dependency, off `get_current_manager`, off `get_admin`, or
    off a machine door asking for a write scope — and a test says so, the way
    a scope opening no route is a bug the tests catch.
    """
    if not user.can_write():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account may read Ganesh, not write into it.",
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


async def get_admin(
    user: User = Depends(get_current_user),
) -> User:
    """Restricts access to administrators.

    The one door above the manager's, and the only one the administration
    screen opens on.
    """
    if not user.can_administrate():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action is reserved for administrators.",
        )
    return user
