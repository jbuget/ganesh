"""Validating tokens issued by Microsoft Entra ID.

Public keys are fetched from the tenant's JWKS endpoint and cached: Entra
rotates them rarely, and one network call per request would be a needless
cost.
"""

import logging
from typing import Any

import httpx
from jose import jwt
from jose.exceptions import JWTError

from src.shared.exceptions.domain_exceptions import ForbiddenActionError

logger = logging.getLogger(__name__)

JWKS_CACHE: dict[str, dict[str, Any]] = {}


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

    async def _jwks(self) -> dict[str, Any]:
        cached = JWKS_CACHE.get(self._tenant_id)
        if cached is not None:
            return cached
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(self._jwks_url)
            response.raise_for_status()
            keys: dict[str, Any] = response.json()
        JWKS_CACHE[self._tenant_id] = keys
        return keys

    async def validate(self, token: str) -> dict[str, Any]:
        """Returns the token claims, or denies access."""
        try:
            claims: dict[str, Any] = jwt.decode(
                token,
                await self._jwks(),
                algorithms=["RS256"],
                audience=self._client_id,
                issuer=self._issuer,
            )
        except JWTError as error:
            logger.warning("Jeton Entra refuse : %s", error)
            raise ForbiddenActionError("Jeton d'authentification invalide.") from error
        return claims
