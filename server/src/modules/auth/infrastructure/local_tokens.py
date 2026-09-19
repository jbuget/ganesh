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

import hmac
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import jwt
from jose.exceptions import JWTError

from src.shared.exceptions.domain_exceptions import ForbiddenActionError

ALGORITHM = "HS256"
ISSUER = "ganesh-local"

#: A day: long enough not to sign in twice a morning, short enough that a
#: token left behind on a machine does not outlive the week.
DEFAULT_LIFETIME_SECONDS = 60 * 60 * 24


def check_credentials(
    login: str,
    password: str,
    expected_login: str | None,
    expected_password: str | None,
) -> bool:
    """Whether these credentials open the door.

    An unset password closes the door rather than opening it to whoever leaves
    the field empty. The comparison takes the same time whichever character
    differs: a password must not be guessable one letter at a time.

    Both sides are compared as bytes, because `compare_digest` refuses text
    that is not ASCII — an accented password would raise where it should
    answer, and the 500 that follows tells whoever is trying that this
    password is not like the others.
    """
    if not expected_login or not expected_password:
        return False
    return hmac.compare_digest(
        login.encode("utf-8"), expected_login.encode("utf-8")
    ) and hmac.compare_digest(
        password.encode("utf-8"), expected_password.encode("utf-8")
    )


class LocalTokenService:
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
        except JWTError as error:
            raise ForbiddenActionError("Invalid authentication token.") from error
        return claims
