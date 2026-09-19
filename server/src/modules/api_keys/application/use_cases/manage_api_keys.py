"""Minting, listing and revoking service accounts."""

from datetime import datetime

from src.modules.api_keys.application.dtos.api_key_dto import (
    CreateApiKeyCommand,
    MintedApiKey,
    RevokeApiKeyCommand,
)
from src.modules.api_keys.domain.entities.api_key import ApiKey
from src.modules.api_keys.domain.repositories.api_key_repository import ApiKeyRepository
from src.modules.api_keys.domain.services import key_material
from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError, ValidationError


class CreateApiKeyUseCase:
    """Mints a key and hands the token over once."""

    def __init__(
        self,
        keys: ApiKeyRepository,
        users: UserRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._keys = keys
        self._users = users
        self._audit_logs = audit_logs

    async def execute(self, command: CreateApiKeyCommand) -> MintedApiKey:
        owner = await self._users.get_by_id(command.owner_id)
        if owner is None:
            raise EntityNotFoundError("The owner cannot be found.")
        # A key is only as alive as the person answering for it: minting one
        # against an account already cut would produce a key dead on arrival.
        if not owner.is_active:
            raise ValidationError("A deactivated teammate cannot own a key.")

        public_id, secret, token = key_material.generate()
        key = await self._keys.add(
            ApiKey(
                id=None,
                name=command.name,
                public_id=public_id,
                secret_hash=key_material.hash_secret(secret),
                owner_id=command.owner_id,
                created_by=command.actor_id,
                scopes=command.scopes,
                expires_at=command.expires_at,
            )
        )

        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.API_KEY_CREATE,
                actor_id=command.actor_id,
                target_user_id=command.owner_id,
                new_value=key_material.masked(public_id),
                payload={
                    "name": key.name,
                    "scopes": sorted(scope.value for scope in key.scopes),
                },
            )
        )
        return MintedApiKey(key=key, token=token, owner=owner)


class ListApiKeysUseCase:
    """Every key, with the people behind it.

    Read by the whole team: a key nobody looks at is a key nobody notices has
    been idle for months.
    """

    def __init__(self, keys: ApiKeyRepository, users: UserRepository) -> None:
        self._keys = keys
        self._users = users

    async def execute(self) -> tuple[list[ApiKey], dict[int, User]]:
        keys = await self._keys.list_all()
        people = {
            user.id: user
            for user in await self._users.list_all(include_inactive=True)
            if user.id is not None
        }
        return keys, people


class RevokeApiKeyUseCase:
    """Cuts a key. Immediate and final."""

    def __init__(
        self,
        keys: ApiKeyRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._keys = keys
        self._audit_logs = audit_logs

    async def execute(self, command: RevokeApiKeyCommand) -> ApiKey:
        key = await self._keys.get_by_id(command.key_id)
        if key is None:
            raise EntityNotFoundError("The key cannot be found.")

        key.revoke(by=command.actor_id, at=datetime.now())
        await self._keys.update(key)

        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.API_KEY_REVOKE,
                actor_id=command.actor_id,
                target_user_id=key.owner_id,
                old_value=key_material.masked(key.public_id),
                payload={"name": key.name},
            )
        )
        return key
