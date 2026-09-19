"""The fallback door, as a route.

It only exists when Entra is expressly turned off: with Entra on, the route
answers « not found » rather than « forbidden ». Two doors open at once would
be one too many, and a door one can feel is a door one can push.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.core.config import Settings, get_settings
from src.modules.auth.infrastructure.local_tokens import check_credentials
from src.modules.auth.presentation.dependencies import local_token_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


class LocalSignInRequest(BaseModel):
    """What the sign-in form sends."""

    login: str
    password: str


class LocalSignInResponse(BaseModel):
    """The token the door hands over, which the API verifies like any other."""

    access_token: str


@router.post("/local", response_model=LocalSignInResponse, operation_id="signInLocally")
async def sign_in_locally(
    payload: LocalSignInRequest,
    settings: Settings = Depends(get_settings),
) -> LocalSignInResponse:
    """Opens the fallback door, while Entra has yet to know this application."""
    if settings.auth_entra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La connexion locale n'existe pas sur cette instance.",
        )

    if not check_credentials(
        payload.login, payload.password, settings.auth_login, settings.auth_password
    ):
        # One refusal for both fields: naming which one was wrong would tell
        # whoever is trying that they already hold half of it.
        logger.warning("Connexion locale refusée pour « %s ».", payload.login)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiant ou mot de passe incorrect.",
        )

    return LocalSignInResponse(access_token=local_token_service(settings).issue())
