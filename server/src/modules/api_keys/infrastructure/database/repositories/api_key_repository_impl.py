"""SQLAlchemy implementation of the ApiKeyRepository port."""

from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.api_keys.domain.entities.api_key import ApiKey, ApiKeyScope
from src.modules.api_keys.domain.repositories.api_key_repository import ApiKeyRepository
from src.modules.api_keys.infrastructure.database.models.api_key_models import (
    ApiKeyModel,
    ApiKeyScopeModel,
)


def to_entity(model: ApiKeyModel, scopes: list[ApiKeyScope]) -> ApiKey:
    return ApiKey(
        id=model.id,
        name=model.name,
        public_id=model.public_id,
        secret_hash=model.secret_hash,
        owner_id=model.owner_id,
        created_by=model.created_by,
        scopes=scopes,
        created_at=model.created_at,
        expires_at=model.expires_at,
        last_used_at=model.last_used_at,
        revoked_at=model.revoked_at,
        revoked_by=model.revoked_by,
    )


class SqlApiKeyRepository(ApiKeyRepository):
    """Persists the service accounts and the scopes they carry."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, key: ApiKey) -> ApiKey:
        model = ApiKeyModel(
            name=key.name,
            public_id=key.public_id,
            secret_hash=key.secret_hash,
            owner_id=key.owner_id,
            created_by=key.created_by,
            created_at=key.created_at,
            expires_at=key.expires_at,
        )
        self._session.add(model)
        await self._session.flush()
        key.id = model.id
        await self._write_scopes(model.id, key.scopes)
        return key

    async def get_by_id(self, key_id: int) -> ApiKey | None:
        model = await self._session.get(ApiKeyModel, key_id)
        if model is None:
            return None
        return to_entity(model, await self._read_scopes(model.id))

    async def get_by_public_id(self, public_id: str) -> ApiKey | None:
        result = await self._session.execute(
            select(ApiKeyModel).where(ApiKeyModel.public_id == public_id)
        )
        model = result.scalars().first()
        if model is None:
            return None
        return to_entity(model, await self._read_scopes(model.id))

    async def list_all(self) -> list[ApiKey]:
        result = await self._session.execute(
            select(ApiKeyModel).order_by(ApiKeyModel.created_at.desc())
        )
        models = list(result.scalars().all())
        if not models:
            return []

        # The scopes of every key in one go: a dozen keys would otherwise make
        # a dozen round trips for three rows each.
        by_key: dict[int, list[ApiKeyScope]] = {model.id: [] for model in models}
        rows = await self._session.execute(
            select(ApiKeyScopeModel).where(
                ApiKeyScopeModel.api_key_id.in_(by_key.keys())
            )
        )
        for row in rows.scalars().all():
            by_key[row.api_key_id].append(row.scope)

        return [to_entity(model, sorted(by_key[model.id])) for model in models]

    async def update(self, key: ApiKey) -> None:
        if key.id is None:
            return
        model = await self._session.get(ApiKeyModel, key.id)
        if model is None:
            return
        model.name = key.name
        model.expires_at = key.expires_at
        model.last_used_at = key.last_used_at
        model.revoked_at = key.revoked_at
        model.revoked_by = key.revoked_by
        await self._write_scopes(key.id, key.scopes)
        await self._session.flush()

    async def record_use(self, key_id: int, used_at: datetime) -> None:
        await self._session.execute(
            update(ApiKeyModel)
            .where(ApiKeyModel.id == key_id)
            .values(last_used_at=used_at)
        )

    async def _read_scopes(self, key_id: int) -> list[ApiKeyScope]:
        result = await self._session.execute(
            select(ApiKeyScopeModel.scope)
            .where(ApiKeyScopeModel.api_key_id == key_id)
            .order_by(ApiKeyScopeModel.scope)
        )
        return list(result.scalars().all())

    async def _write_scopes(self, key_id: int, scopes: list[ApiKeyScope]) -> None:
        await self._session.execute(
            delete(ApiKeyScopeModel).where(ApiKeyScopeModel.api_key_id == key_id)
        )
        for scope in dict.fromkeys(scopes):
            await self._session.execute(
                insert(ApiKeyScopeModel).values(api_key_id=key_id, scope=scope)
            )
