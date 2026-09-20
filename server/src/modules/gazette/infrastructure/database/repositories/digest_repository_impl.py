"""SQLAlchemy implementation of the DigestRepository port."""

from dataclasses import replace
from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.gazette.domain.entities.digest import Digest, DigestVersion
from src.modules.gazette.domain.entities.prose import Prose
from src.modules.gazette.domain.repositories.digest_repository import DigestRepository
from src.modules.gazette.infrastructure.database.brief_json import from_json, to_json
from src.modules.gazette.infrastructure.database.models.gazette_digest_model import (
    GazetteDigestModel,
)


def to_entity(model: GazetteDigestModel) -> Digest:
    return Digest(
        id=model.id,
        month=model.month,
        version=model.version,
        brief=from_json(model.month, model.brief),
        generated_at=model.generated_at,
        requested_by=model.requested_by,
        prose=_prose(model),
    )


def _prose(model: GazetteDigestModel) -> Prose | None:
    """The chapeau, if the digest was generated with one.

    Read back through the same rule it was written under: a text that would
    be refused today is not served because it was stored yesterday.
    """
    if not model.prose or not model.prose_model:
        return None
    return Prose.accepted(model.prose, model.prose_model)


class SqlDigestRepository(DigestRepository):
    """Persists the digests of the gazette."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest(self, month: date) -> Digest | None:
        result = await self._session.execute(
            select(GazetteDigestModel)
            .where(GazetteDigestModel.month == month)
            .order_by(GazetteDigestModel.version.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return to_entity(model) if model else None

    async def get_version(self, month: date, version: int) -> Digest | None:
        result = await self._session.execute(
            select(GazetteDigestModel).where(
                and_(
                    GazetteDigestModel.month == month,
                    GazetteDigestModel.version == version,
                )
            )
        )
        model = result.scalar_one_or_none()
        return to_entity(model) if model else None

    async def list_versions(self, month: date) -> list[DigestVersion]:
        result = await self._session.execute(
            select(
                GazetteDigestModel.version,
                GazetteDigestModel.generated_at,
                GazetteDigestModel.requested_by,
            )
            .where(GazetteDigestModel.month == month)
            .order_by(GazetteDigestModel.version.desc())
        )
        return [
            DigestVersion(
                version=version, generated_at=generated_at, requested_by=requested_by
            )
            for version, generated_at, requested_by in result.all()
        ]

    async def add(self, digest: Digest) -> Digest:
        model = GazetteDigestModel(
            month=digest.month,
            version=digest.version,
            generated_at=digest.generated_at,
            requested_by=digest.requested_by,
            brief=to_json(digest.brief),
            prose=digest.prose.text if digest.prose else None,
            prose_model=digest.prose.model if digest.prose else None,
        )
        self._session.add(model)
        await self._session.flush()
        return replace(digest, id=model.id)
