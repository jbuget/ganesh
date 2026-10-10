"""Turning a digest into what the screen reads."""

from src.modules.gazette.application.dtos.gazette_dtos import DigestView
from src.modules.gazette.domain.entities.brief import Tally
from src.modules.gazette.domain.entities.chapter import Chapter
from src.modules.gazette.domain.entities.digest import DigestVersion
from src.modules.gazette.domain.entities.focus import ProjectFocus
from src.modules.gazette.domain.entities.highlight import Highlight
from src.modules.gazette.domain.entities.movement import Movement
from src.modules.gazette.domain.entities.spotlight import Spotlight
from src.modules.gazette.domain.services.chaptering import into_chapters
from src.modules.gazette.presentation.api.schemas.gazette_schemas import (
    ChapterResponse,
    DigestResponse,
    DigestVersionResponse,
    HighlightResponse,
    MovementResponse,
    SpotlightResponse,
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
        prose_model=_model_of(view),
        spotlights=_to_spotlights(view),
        tally=to_tally(view.brief.tally),
        chapters=[
            _to_chapter(chapter) for chapter in into_chapters(view.brief.movements)
        ],
        highlights=[_to_highlight(highlight) for highlight in view.brief.highlights],
        versions=[_to_version(version) for version in view.versions],
    )


def _model_of(view: DigestView) -> str | None:
    """Which model wrote what is shown: the editorial's, else a spotlight's."""
    if view.prose:
        return view.prose.model
    return view.spotlights[0].model if view.spotlights else None


def _to_spotlights(view: DigestView) -> list[SpotlightResponse]:
    """Each spotlight with the figures of its project, from the same brief."""
    focus = {one.project_id: one for one in view.brief.focus}
    return [
        to_spotlight(spotlight, focus[spotlight.project_id])
        for spotlight in view.spotlights
        if spotlight.project_id in focus
    ]


def to_spotlight(spotlight: Spotlight, focus: ProjectFocus) -> SpotlightResponse:
    return SpotlightResponse(
        project_id=spotlight.project_id,
        label=spotlight.label,
        text=spotlight.text,
        status=focus.status,
        went_live=focus.went_live,
        updates_posted=focus.updates_posted,
        days_declared=focus.days_declared,
        contributors=focus.contributors,
    )


def to_tally(tally: Tally) -> TallyResponse:
    return TallyResponse(
        projects_created=tally.projects_created,
        projects_archived=tally.projects_archived,
        phase_changes=tally.phase_changes,
        news_posted=tally.news_posted,
        months_validated=tally.months_validated,
        requests_filed=tally.requests_filed,
        requests_converted=tally.requests_converted,
    )


def _to_chapter(chapter: Chapter) -> ChapterResponse:
    return ChapterResponse(
        of=chapter.of,
        project_id=chapter.project_id,
        label=chapter.label,
        movements=[_to_movement(movement) for movement in chapter.movements],
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
