"""SQLAlchemy implementation of the DigestRepository port."""

from dataclasses import replace
from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.gazette.domain.entities.digest import Digest, DigestVersion
from src.modules.gazette.domain.entities.prose import Prose
from src.modules.gazette.domain.entities.spotlight import Spotlight
from src.modules.gazette.domain.repositories.digest_repository import DigestRepository
from src.modules.gazette.domain.services.figures import allowed_figures
from src.modules.gazette.infrastructure.database.brief_json import from_json, to_json
from src.modules.gazette.infrastructure.database.models.gazette_digest_model import (
    GazetteDigestModel,
)
from src.shared.exceptions.domain_exceptions import ConflictError


def to_entity(model: GazetteDigestModel) -> Digest:
    brief = from_json(model.month, model.brief)
    allowed = allowed_figures(brief)
    return Digest(
        id=model.id,
        month=model.month,
        version=model.version,
        brief=brief,
        generated_at=model.generated_at,
        requested_by=model.requested_by,
        prose=_prose(model, allowed),
        spotlights=_spotlights(model, allowed),
    )


def _prose(model: GazetteDigestModel, allowed: frozenset[str]) -> Prose | None:
    """The editorial, if the digest was generated with one.

    Read back through the same rule it was written under, against the figures
    of the facts stored beside it: a text that would be refused today is not
    served because it was stored yesterday.
    """
    if not model.prose or not model.prose_model:
        return None
    return Prose.accepted(model.prose, model.prose_model, allowed)


def _spotlights(
    model: GazetteDigestModel, allowed: frozenset[str]
) -> tuple[Spotlight, ...]:
    """The spotlights, each held to the same rule as the editorial."""
    return tuple(
        Spotlight(row["project_id"], row["label"], row["text"], row["model"])
        for row in model.spotlights or []
        if Prose.accepted(row["text"], row["model"], allowed)
    )


class SqlDigestRepository(DigestRepository):
    """Persists the digests of the gazette."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, digest_id: int) -> Digest | None:
        model = await self._session.get(GazetteDigestModel, digest_id)
        return to_entity(model) if model else None

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
            spotlights=[
                {
                    "project_id": s.project_id,
                    "label": s.label,
                    "text": s.text,
                    "model": s.model,
                }
                for s in digest.spotlights
            ],
        )
        # In a savepoint: losing the race for a version number must not poison
        # the whole transaction, and what comes back is a refusal that says so.
        try:
            async with self._session.begin_nested():
                self._session.add(model)
                await self._session.flush()
        except IntegrityError as error:
            raise ConflictError(
                "Somebody has just generated a digest of this month: "
                "read their version rather than writing another beside it."
            ) from error
        return replace(digest, id=model.id)
