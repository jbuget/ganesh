"""Turning Entra claims into an application identity."""

from typing import Any

from src.modules.users.application.dtos.user_dto import EntraIdentity
from src.shared.exceptions.domain_exceptions import ForbiddenActionError

#: Entra puts the address in one of these claims depending on account type.
EMAIL_CLAIMS = ("preferred_username", "email", "upn")


def identity_from_claims(claims: dict[str, Any]) -> EntraIdentity:
    """Extracts the identity from a valid token."""
    oid = claims.get("oid") or claims.get("sub")
    if not oid:
        raise ForbiddenActionError("Token without an object id.")

    email = next((claims[key] for key in EMAIL_CLAIMS if claims.get(key)), None)
    if not email:
        raise ForbiddenActionError("Token without an email address.")

    return EntraIdentity(
        oid=str(oid),
        email=str(email),
        display_name=str(claims.get("name") or email),
    )
