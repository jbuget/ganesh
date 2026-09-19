"""Schemas of the service accounts."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.modules.api_keys.domain.entities.api_key import (
    NAME_MAX_LENGTH,
    ApiKeyScope,
    ApiKeyState,
)


class ApiKeyOwnerResponse(BaseModel):
    """A person named on a key: its owner, or whoever minted or cut it."""

    id: int
    display_name: str
    initials: str


class ApiKeyResponse(BaseModel):
    """A key as the table shows it.

    It carries no secret, by construction: `masked` is the public half alone,
    a lookup handle that helps nobody use the key. That is what makes the
    table safe to show the whole team.
    """

    id: int
    name: str
    #: `jns_<public_id>`. All that is ever shown again.
    masked: str
    scopes: list[ApiKeyScope]
    owner: ApiKeyOwnerResponse
    created_by: ApiKeyOwnerResponse
    created_at: datetime
    expires_at: datetime | None
    last_used_at: datetime | None
    revoked_at: datetime | None
    revoked_by: ApiKeyOwnerResponse | None
    #: What the badge reads. Derived by the entity, not recomputed anywhere.
    state: ApiKeyState


class CreateApiKeyRequest(BaseModel):
    """Minting a key."""

    name: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)
    owner_id: int
    scopes: list[ApiKeyScope] = Field(min_length=1)
    expires_at: datetime | None = None


class UpdateApiKeyRequest(BaseModel):
    """Partial change: a field left out is a field left alone.

    The secret, the owner and the expiry are not here. Reissuing a secret is
    minting a key; the other two are reasons to mint one too.
    """

    name: str | None = Field(default=None, min_length=1, max_length=NAME_MAX_LENGTH)
    scopes: list[ApiKeyScope] | None = Field(default=None, min_length=1)


class MintedApiKeyResponse(BaseModel):
    """The one and only response that carries a whole key.

    Nothing stores the token, and no route hands it over a second time. There
    is no « reveal » endpoint because there is nothing left to reveal.
    """

    key: ApiKeyResponse
    token: str
