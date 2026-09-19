"""Translating service accounts into API schemas.

Translation only: what a key is worth is decided by the entity, never
recomputed here. A rule written in two places is a rule that will disagree with
itself.
"""

from datetime import datetime

from src.modules.api_keys.domain.entities.api_key import ApiKey
from src.modules.api_keys.domain.services import key_material
from src.modules.api_keys.presentation.api.schemas.api_key_schemas import (
    ApiKeyOwnerResponse,
    ApiKeyResponse,
)
from src.modules.users.domain.entities.user import User
from src.shared.utils.initials import initials


def to_owner_response(user: User | None) -> ApiKeyOwnerResponse | None:
    if user is None or user.id is None:
        return None
    return ApiKeyOwnerResponse(
        id=user.id,
        display_name=user.display_name,
        initials=initials(user.display_name),
    )


#: A person the table names but whose account has since been erased. Rather
#: than hiding the line, the key still says a human was there.
UNKNOWN = ApiKeyOwnerResponse(id=0, display_name="Compte supprimé", initials="?")


def to_api_key_response(
    key: ApiKey, people: dict[int, User], now: datetime
) -> ApiKeyResponse:
    """`now` is passed in, never read here: a mapper does not own a clock."""
    assert key.id is not None
    revoked_by = (
        to_owner_response(people.get(key.revoked_by))
        if key.revoked_by is not None
        else None
    )
    return ApiKeyResponse(
        id=key.id,
        name=key.name,
        masked=key_material.masked(key.public_id),
        scopes=key.scopes,
        owner=to_owner_response(people.get(key.owner_id)) or UNKNOWN,
        created_by=to_owner_response(people.get(key.created_by)) or UNKNOWN,
        created_at=key.created_at,
        expires_at=key.expires_at,
        last_used_at=key.last_used_at,
        revoked_at=key.revoked_at,
        revoked_by=revoked_by,
        state=key.state_at(now),
    )
