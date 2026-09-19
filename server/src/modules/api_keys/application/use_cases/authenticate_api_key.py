"""Letting a machine in, for one scope at a time."""

from dataclasses import dataclass
from datetime import datetime

from src.modules.api_keys.domain.entities.api_key import ApiKey, ApiKeyScope
from src.modules.api_keys.domain.repositories.api_key_repository import ApiKeyRepository
from src.modules.api_keys.domain.services import key_material
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import ForbiddenActionError


@dataclass(frozen=True)
class MachineCaller:
    """The machine that called, and the human who answers for it.

    The owner is what the audit records: nothing in the use cases has to learn
    about machines, and the trace still says who is accountable. The key is
    named alongside, in the payload.
    """

    key: ApiKey
    owner: User

    @property
    def actor_id(self) -> int:
        assert self.owner.id is not None
        return self.owner.id


class AuthenticateApiKeyUseCase:
    """Turns a bearer token into a caller, or into nothing at all.

    Unknown, malformed, expired, revoked, owner deactivated: all five come back
    as `None`, and the caller answers `401` to every one of them. Telling them
    apart would hand an attacker a way to enumerate.

    A valid key that lacks the scope is another matter: it raises, and the
    caller answers `403`. There the distinction is useful — whoever holds a
    real key needs to know what to ask for.
    """

    def __init__(self, keys: ApiKeyRepository, users: UserRepository) -> None:
        self._keys = keys
        self._users = users

    async def execute(self, token: str, scope: ApiKeyScope) -> MachineCaller | None:
        parsed = key_material.parse(token)
        if parsed is None:
            return None
        public_id, secret = parsed

        key = await self._keys.get_by_public_id(public_id)
        if key is None:
            return None
        if not key_material.matches(secret, key.secret_hash):
            return None

        now = datetime.now()
        if not key.is_usable(now):
            return None

        owner = await self._users.get_by_id(key.owner_id)
        if owner is None or not owner.is_active:
            return None

        if not key.grants(scope):
            raise ForbiddenActionError(
                f"This key does not carry the scope « {scope.value} »."
            )

        # Stamped through a window: without it the column would measure HTTP
        # traffic rather than use, and write a row on every call.
        if key.record_use(now):
            await self._keys.update(key)

        return MachineCaller(key=key, owner=owner)
