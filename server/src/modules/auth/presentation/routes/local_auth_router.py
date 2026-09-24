"""The fallback door, as a route.

It only exists when Entra is expressly turned off: with Entra on, the route
answers « not found » rather than « forbidden ». Two doors open at once would
be one too many, and a door one can feel is a door one can push.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.modules.auth.application.use_cases.sign_in_locally import SignInLocallyUseCase
from src.modules.auth.domain.entities.sign_in import InvalidCredentialsError
from src.modules.auth.presentation.dependencies import get_sign_in_locally_use_case

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
    use_case: SignInLocallyUseCase = Depends(get_sign_in_locally_use_case),
) -> LocalSignInResponse:
    """Opens the fallback door, while Entra has yet to know this application.

    The door being shut answers 404 on its own: `FallbackDoorClosedError`
    narrows `EntityNotFoundError`, which the shared handler already maps.
    Refused credentials are the one case this route translates itself — 401 is
    the status no shared exception carries, because signing in is the only
    place it means anything.
    """
    try:
        return LocalSignInResponse(
            access_token=await use_case.execute(payload.login, payload.password)
        )
    except InvalidCredentialsError as refusal:
        # One refusal for both fields: naming which one was wrong would tell
        # whoever is trying that they already hold half of it.
        logger.warning("Connexion locale refusée pour « %s ».", payload.login)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(refusal)
        ) from refusal
