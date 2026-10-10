"""Turning a share link, and what it opens, into what the screen reads."""

from src.modules.gazette.application.dtos.gazette_dtos import ShareLinkView
from src.modules.gazette.domain.entities.public_digest import PublicDigest
from src.modules.gazette.presentation.api.mappers.gazette_mapper import (
    to_spotlight,
    to_tally,
)
from src.modules.gazette.presentation.api.schemas.gazette_schemas import (
    PublicDigestResponse,
    ShareLinkResponse,
)


def to_share_link_response(view: ShareLinkView) -> ShareLinkResponse:
    link = view.link
    assert link.id is not None
    return ShareLinkResponse(
        id=link.id,
        token=link.token,
        created_by=view.created_by,
        created_at=link.created_at,
    )


def to_public_digest_response(digest: PublicDigest) -> PublicDigestResponse:
    focus = {one.project_id: one for one in digest.focus}
    return PublicDigestResponse(
        month=digest.month,
        version=digest.version,
        generated_at=digest.generated_at,
        prose=digest.prose.text if digest.prose else None,
        prose_model=digest.model,
        spotlights=[
            to_spotlight(spotlight, focus[spotlight.project_id])
            for spotlight in digest.spotlights
            if spotlight.project_id in focus
        ],
        tally=to_tally(digest.tally),
        went_live=[highlight.label for highlight in digest.went_live],
        names=list(digest.names),
    )
