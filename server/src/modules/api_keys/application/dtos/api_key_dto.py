"""Commands acting on the service accounts."""

from dataclasses import dataclass
from datetime import datetime

from src.modules.api_keys.domain.entities.api_key import ApiKey, ApiKeyScope
from src.modules.users.domain.entities.user import User


@dataclass(frozen=True)
class CreateApiKeyCommand:
    """Minting a key. Managers only — the route sees to that."""

    actor_id: int
    name: str
    owner_id: int
    scopes: list[ApiKeyScope]
    expires_at: datetime | None = None


@dataclass(frozen=True)
class RevokeApiKeyCommand:
    """Cutting a key for good."""

    actor_id: int
    key_id: int


@dataclass(frozen=True)
class MintedApiKey:
    """A freshly minted key and its secret, together, once.

    The token travels no further than the response that carries it: nothing
    stores it, and no route ever hands it over a second time.
    """

    key: ApiKey
    token: str
    #: Named on the key, and already looked up while minting it.
    owner: User
