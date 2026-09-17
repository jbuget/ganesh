"""Authentification des requetes et resolution de l'utilisateur courant."""

import logging

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.database import get_db
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

#: Identite utilisee quand l'authentification est desactivee en developpement.
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
    """Resout l'utilisateur courant, en le provisionnant au besoin.

    Avec `REQUIRE_AUTH=false`, une identite de developpement est utilisee : cela
    permet de travailler sans avoir declare l'URI de redirection cote Entra.
    Ce mode ne doit jamais etre actif en production.
    """
    provision = ProvisionUserUseCase(users=SqlUserRepository(session))

    if not settings.require_auth:
        logger.warning("Authentification desactivee : identite de developpement.")
        user = await provision.execute(DEV_IDENTITY)
        await session.commit()
        return user

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton d'authentification manquant.",
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

    if not user.actif:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte est desactive.",
        )
    return user


async def get_current_manager(
    user: User = Depends(get_current_user),
) -> User:
    """Restreint l'acces aux managers."""
    if not user.can_manage_teammates():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cette action est reservee aux managers.",
        )
    return user
