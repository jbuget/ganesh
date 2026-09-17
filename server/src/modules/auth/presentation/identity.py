"""Traduction des revendications Entra en identite applicative."""

from typing import Any

from src.modules.users.application.dtos.user_dto import EntraIdentity
from src.shared.exceptions.domain_exceptions import ForbiddenActionError

#: Entra place l'adresse dans l'une de ces revendications selon le type de compte.
EMAIL_CLAIMS = ("preferred_username", "email", "upn")


def identity_from_claims(claims: dict[str, Any]) -> EntraIdentity:
    """Extrait l'identite d'un jeton valide."""
    oid = claims.get("oid") or claims.get("sub")
    if not oid:
        raise ForbiddenActionError("Jeton sans identifiant d'objet.")

    email = next((claims[key] for key in EMAIL_CLAIMS if claims.get(key)), None)
    if not email:
        raise ForbiddenActionError("Jeton sans adresse email.")

    return EntraIdentity(
        oid=str(oid),
        email=str(email),
        display_name=str(claims.get("name") or email),
    )
