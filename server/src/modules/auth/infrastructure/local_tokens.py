"""The way in when Entra is not there yet.

Declaring an application in Entra takes as long as it takes, and a product
should not wait on that to be used. This is the fallback: one account, named
in the environment, signing in with a password — and a token this service
issues itself, which the API verifies exactly as it verifies Entra's.

It is a back door, so it is built like one: it only opens when Entra is
expressly turned off, it opens onto a single account, and it refuses to open
at all if no password was set. What it issues carries the same claims Entra
would, so nothing downstream has to know which door was used.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt import PyJWTError

from src.modules.auth.domain.repositories.token_issuer import TokenIssuer
from src.shared.exceptions.domain_exceptions import ForbiddenActionError

ALGORITHM = "HS256"
ISSUER = "ganesh-local"

#: A day: long enough not to sign in twice a morning, short enough that a
#: token left behind on a machine does not outlive the week.
DEFAULT_LIFETIME_SECONDS = 60 * 60 * 24


class LocalTokenService(TokenIssuer):
    """Issues and verifies the tokens of the fallback door."""

    def __init__(self, secret_key: str, email: str) -> None:
        self._secret_key = secret_key
        self._email = email

    def issue(self, lifetime_seconds: int = DEFAULT_LIFETIME_SECONDS) -> str:
        """A token naming the one account this door opens onto."""
        now = datetime.now(tz=UTC)
        token: str = jwt.encode(
            {
                # The same claims Entra sends, so provisioning reads one shape:
                # a stable id, an address, a name.
                "oid": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{ISSUER}:{self._email}")),
                "preferred_username": self._email,
                "name": self._email,
                "iss": ISSUER,
                "iat": now,
                "exp": now + timedelta(seconds=lifetime_seconds),
            },
            self._secret_key,
            algorithm=ALGORITHM,
        )
        return token

    def validate(self, token: str) -> dict[str, Any]:
        """The claims of a token we issued, or no way in."""
        try:
            claims: dict[str, Any] = jwt.decode(
                token,
                self._secret_key,
                algorithms=[ALGORITHM],
                issuer=ISSUER,
                # Nothing here is meant for an audience: this token is for us.
                options={"verify_aud": False},
            )
        except PyJWTError as error:
            raise ForbiddenActionError("Invalid authentication token.") from error
        return claims
