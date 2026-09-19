"""Minting, listing and revoking service accounts."""

from datetime import datetime

from src.modules.api_keys.application.dtos.api_key_dto import (
    ApiKeyListing,
    CreateApiKeyCommand,
    MintedApiKey,
    NamedApiKey,
    RevokeApiKeyCommand,
    UpdateApiKeyCommand,
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


async def people_named_by(users: UserRepository, key: ApiKey) -> dict[int, User]:
    """The two or three humans a key names, and no one else.

    Looked up one by one rather than by reading the whole directory: a key
    names an owner, whoever minted it and, sometimes, whoever cut it.
    """
    named: dict[int, User] = {}
    for user_id in (key.owner_id, key.created_by, key.revoked_by):
        if user_id is None or user_id in named:
            continue
        user = await users.get_by_id(user_id)
        if user is not None:
            named[user_id] = user
    return named


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
        return MintedApiKey(
            key=key,
            token=token,
            people=await people_named_by(self._users, key),
        )


class ListApiKeysUseCase:
    """Every key, with the people behind it.

    Read by the whole team: a key nobody looks at is a key nobody notices has
    been idle for months.
    """

    def __init__(self, keys: ApiKeyRepository, users: UserRepository) -> None:
        self._keys = keys
        self._users = users

    async def execute(self) -> ApiKeyListing:
        keys = await self._keys.list_all()
        # The whole directory in one go: dozens of keys naming the same
        # handful of people would otherwise be dozens of lookups.
        people = {
            user.id: user
            for user in await self._users.list_all(include_inactive=True)
            if user.id is not None
        }
        return ApiKeyListing(keys=keys, people=people)


class UpdateApiKeyUseCase:
    """Corrects what a key is called and what it opens.

    Nothing else: the secret is not reissued, the owner is not swapped and the
    expiry is not moved. Those are reasons to mint a new key.
    """

    def __init__(
        self,
        keys: ApiKeyRepository,
        users: UserRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._keys = keys
        self._users = users
        self._audit_logs = audit_logs

    async def execute(self, command: UpdateApiKeyCommand) -> NamedApiKey:
        key = await self._keys.get_by_id(command.key_id)
        if key is None:
            raise EntityNotFoundError("The key cannot be found.")

        changes: list[tuple[str, str, str]] = []

        if command.name is not None and command.name.strip() != key.name:
            changes.append(("name", key.name, command.name.strip()))
            key.rename(command.name)

        if command.scopes is not None:
            before = sorted(scope.value for scope in key.scopes)
            after = sorted(scope.value for scope in command.scopes)
            if before != after:
                changes.append(("scopes", ", ".join(before), ", ".join(after)))
            # Replayed even when equal: the entity is what refuses an empty
            # list, and a screen sending one must be told.
            key.set_scopes(command.scopes)

        named = NamedApiKey(key=key, people=await people_named_by(self._users, key))
        if not changes:
            return named

        await self._keys.update(key)

        # One trace per field, as editing a mission already does.
        for field, before_value, after_value in changes:
            await self._audit_logs.add(
                AuditLog(
                    action=AuditAction.API_KEY_UPDATE,
                    actor_id=command.actor_id,
                    target_user_id=key.owner_id,
                    old_value=before_value[:64],
                    new_value=after_value[:64],
                    payload={
                        "field": field,
                        "api_key": key_material.masked(key.public_id),
                    },
                )
            )
        return named


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
