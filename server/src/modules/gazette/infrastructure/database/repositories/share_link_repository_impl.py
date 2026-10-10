"""SQLAlchemy implementation of the ShareLinkRepository port."""

from dataclasses import replace

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.gazette.domain.entities.share_link import ShareLink
from src.modules.gazette.domain.repositories.share_link_repository import (
    ShareLinkRepository,
)
from src.modules.gazette.infrastructure.database.models.gazette_share_link_model import (
    GazetteShareLinkModel,
)


def to_entity(model: GazetteShareLinkModel) -> ShareLink:
    return ShareLink(
        id=model.id,
        digest_id=model.digest_id,
        token=model.token,
        created_by_id=model.created_by_id,
        created_at=model.created_at,
        revoked_at=model.revoked_at,
    )


class SqlShareLinkRepository(ShareLinkRepository):
    """Persists the links that open a digest."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, link: ShareLink) -> ShareLink:
        model = GazetteShareLinkModel(
            digest_id=link.digest_id,
            token=link.token,
            created_by_id=link.created_by_id,
            created_at=link.created_at,
            revoked_at=link.revoked_at,
        )
        self._session.add(model)
        await self._session.flush()
        return replace(link, id=model.id)

    async def get(self, link_id: int) -> ShareLink | None:
        model = await self._session.get(GazetteShareLinkModel, link_id)
        return to_entity(model) if model else None

    async def get_by_token(self, token: str) -> ShareLink | None:
        result = await self._session.execute(
            select(GazetteShareLinkModel).where(GazetteShareLinkModel.token == token)
        )
        model = result.scalar_one_or_none()
        return to_entity(model) if model else None

    async def list_open_for_digest(self, digest_id: int) -> list[ShareLink]:
        result = await self._session.execute(
            select(GazetteShareLinkModel)
            .where(
                GazetteShareLinkModel.digest_id == digest_id,
                GazetteShareLinkModel.revoked_at.is_(None),
            )
            .order_by(GazetteShareLinkModel.created_at, GazetteShareLinkModel.id)
        )
        return [to_entity(model) for model in result.scalars().all()]

    async def update(self, link: ShareLink) -> ShareLink:
        model = await self._session.get(GazetteShareLinkModel, link.id)
        if model is not None:
            model.revoked_at = link.revoked_at
            await self._session.flush()
        return link
