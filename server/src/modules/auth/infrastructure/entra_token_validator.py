"""Validating tokens issued by Microsoft Entra ID.

PyJWT rather than python-jose: the latter has not been released since 2021,
and it carries CVE-2024-33663 — an algorithm confusion — on the one code path
every single request goes through. The algorithms were pinned here, which is
what kept that from biting, but a library nobody maintains is not a thing to
keep under the door.

Public keys are fetched from the tenant's JWKS endpoint and cached: Entra
rotates them rarely, and one network call per request would be a needless
cost. A token naming a key the cache does not hold is what a rotation looks
like from here, so the set is fetched again — but no more often than
`UNKNOWN_KEY_COOLDOWN`, or a caller inventing a `kid` per request would turn
every call into a round trip to Entra, on our account.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import httpx
import jwt
from jwt import PyJWK, PyJWKSet, PyJWTError

from src.shared.exceptions.domain_exceptions import ForbiddenActionError
from src.shared.utils import clock

logger = logging.getLogger(__name__)

#: How long a fetched set is trusted before any lookup goes and reads it
#: again. It is also how long a key rotated away keeps being accepted.
JWKS_FRESHNESS = timedelta(hours=1)

#: The shortest gap between two fetches prompted by a `kid` we do not hold.
#: A rotation has to be picked up quickly — an unknown `kid` is what it looks
#: like — but a caller inventing one per request must not turn every call into
#: a round trip to Entra. The cost of the gap is a minute of refusals on a
#: freshly rotated key, and Entra publishes a key well before signing with it.
UNKNOWN_KEY_COOLDOWN = timedelta(minutes=1)


@dataclass(frozen=True)
class _Published:
    """What the tenant published, and when we read it."""

    keys: PyJWKSet
    at: datetime

    def is_stale(self, now: datetime) -> bool:
        return now - self.at >= JWKS_FRESHNESS

    def may_be_read_again(self, now: datetime) -> bool:
        """Whether an unknown `kid` is worth another word with the tenant."""
        return now - self.at >= UNKNOWN_KEY_COOLDOWN


JWKS_CACHE: dict[str, _Published] = {}


async def fetch_jwks(url: str) -> dict[str, Any]:
    """The keys, as the tenant publishes them.

    A function of its own so a test can stand a tenant there without standing
    up an HTTP server.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url)
        response.raise_for_status()
        published: dict[str, Any] = response.json()
        return published


class EntraTokenValidator:
    """Checks the signature and claims of an Entra token."""

    def __init__(self, tenant_id: str, client_id: str) -> None:
        self._tenant_id = tenant_id
        self._client_id = client_id

    @property
    def _jwks_url(self) -> str:
        return (
            f"https://login.microsoftonline.com/{self._tenant_id}/discovery/v2.0/keys"
        )

    @property
    def _issuer(self) -> str:
        return f"https://login.microsoftonline.com/{self._tenant_id}/v2.0"

    async def validate(self, token: str) -> dict[str, Any]:
        """Returns the token claims, or denies access."""
        try:
            key = await self._signing_key(token)
            claims: dict[str, Any] = jwt.decode(
                token,
                key.key,
                algorithms=["RS256"],
                audience=self._client_id,
                issuer=self._issuer,
            )
        except (PyJWTError, httpx.HTTPError) as error:
            logger.warning("Entra token refused: %s", error)
            raise ForbiddenActionError("Invalid authentication token.") from error
        return claims

    async def _signing_key(self, token: str) -> PyJWK:
        """The published key this token names, fetching the set if need be.

        The `kid` is read off an unverified header, which is the only thing it
        can be: it says *which key to check the signature with*, and there is
        no checking anything before that is known. Naming a key proves
        nothing — `jwt.decode` still has to hold.
        """
        kid = jwt.get_unverified_header(token).get("kid")
        if not kid:
            raise PyJWTError("Token naming no signing key.")

        now = clock.now()
        cached = JWKS_CACHE.get(self._tenant_id)
        if cached is not None and not cached.is_stale(now):
            found = _named(cached.keys, kid)
            if found is not None:
                return found
            if not cached.may_be_read_again(now):
                # A key nobody published, and a set read too recently to be
                # worth reading again on this caller's say-so.
                raise PyJWTError(f"Unknown signing key « {kid} ».")

        published = await self._fetch(now)
        found = _named(published.keys, kid)
        if found is None:
            raise PyJWTError(f"Unknown signing key « {kid} ».")
        return found

    async def _fetch(self, now: datetime) -> _Published:
        keys = PyJWKSet.from_dict(await fetch_jwks(self._jwks_url))
        published = _Published(keys=keys, at=now)
        JWKS_CACHE[self._tenant_id] = published
        return published


def _named(keys: PyJWKSet, kid: str) -> PyJWK | None:
    return next((key for key in keys.keys if key.key_id == kid), None)
