"""Turning a digest into what the screen reads."""

from src.modules.gazette.application.dtos.gazette_dtos import DigestView
from src.modules.gazette.domain.entities.brief import Tally
from src.modules.gazette.domain.entities.digest import DigestVersion
from src.modules.gazette.domain.entities.highlight import Highlight
from src.modules.gazette.domain.entities.movement import Movement
from src.modules.gazette.presentation.api.schemas.gazette_schemas import (
    DigestResponse,
    DigestVersionResponse,
    HighlightResponse,
    MovementResponse,
    TallyResponse,
)


def to_digest_response(view: DigestView) -> DigestResponse:
    return DigestResponse(
        month=view.brief.month,
        is_generated=view.is_generated,
        version=view.version,
        generated_at=view.generated_at,
        requested_by=view.requested_by,
        prose=view.prose.text if view.prose else None,
        prose_model=view.prose.model if view.prose else None,
        tally=_to_tally(view.brief.tally),
        movements=[_to_movement(movement) for movement in view.brief.movements],
        highlights=[_to_highlight(highlight) for highlight in view.brief.highlights],
        versions=[_to_version(version) for version in view.versions],
    )


def _to_tally(tally: Tally) -> TallyResponse:
    return TallyResponse(
        projects_created=tally.projects_created,
        projects_archived=tally.projects_archived,
        phase_changes=tally.phase_changes,
        news_posted=tally.news_posted,
        months_validated=tally.months_validated,
    )


def _to_movement(movement: Movement) -> MovementResponse:
    return MovementResponse(
        kind=movement.kind,
        at=movement.at,
        subject=movement.subject,
        project_id=movement.project_id,
        from_status=movement.from_status,
        to_status=movement.to_status,
    )


def _to_highlight(highlight: Highlight) -> HighlightResponse:
    return HighlightResponse(
        kind=highlight.kind,
        tone=highlight.tone,
        project_id=highlight.project_id,
        label=highlight.label,
    )


def _to_version(version: DigestVersion) -> DigestVersionResponse:
    return DigestVersionResponse(
        version=version.version,
        generated_at=version.generated_at,
        requested_by=version.requested_by,
    )
