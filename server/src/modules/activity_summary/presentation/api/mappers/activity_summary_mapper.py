"""Turning the matrix into what the API answers."""

from src.modules.activity_summary.domain.entities.activity_summary import (
    ActivitySummary,
    ActivitySummaryLine,
    Contributor,
)
from src.modules.activity_summary.presentation.api.schemas.activity_summary_schemas import (
    ActivityLineResponse,
    ActivityPeriodResponse,
    ActivitySummaryResponse,
    ContributorResponse,
)
from src.modules.calendar.domain.entities.period import PeriodRange


def to_activity_summary_response(
    summary: ActivitySummary, range_: PeriodRange
) -> ActivitySummaryResponse:
    return ActivitySummaryResponse(
        period=ActivityPeriodResponse(
            range=range_,
            start=summary.period.start,
            end=summary.period.end,
            working_days=summary.period.working_days,
        ),
        contributors=[
            _contributor(someone, summary) for someone in summary.contributors
        ],
        projects=[_line(line, summary) for line in summary.projects],
        off_project=[_line(line, summary) for line in summary.off_project],
        project_days=summary.project_days,
        off_project_days=summary.off_project_days,
        declared_days=summary.declared_days,
        expected_days=summary.expected_days,
        coverage=summary.coverage,
    )


def _contributor(someone: Contributor, summary: ActivitySummary) -> ContributorResponse:
    return ContributorResponse(
        id=someone.id,
        display_name=someone.display_name,
        declared_days=someone.declared_days,
        expected_days=someone.expected_days,
        coverage=someone.coverage,
        missions=_missions_touched_by(someone, summary),
    )


def _missions_touched_by(someone: Contributor, summary: ActivitySummary) -> int:
    """How many missions this person put time on over the window.

    Counted on the rolled-up lines: four packages of one product are one
    mission, which is what the portfolio reading says everywhere else.
    """
    return sum(
        1
        for line in (*summary.projects, *summary.off_project)
        if line.days_of(someone.id) > 0
    )


def _line(line: ActivitySummaryLine, summary: ActivitySummary) -> ActivityLineResponse:
    return ActivityLineResponse(
        project_id=line.project_id,
        label=line.label,
        kind=line.kind,
        status=line.status,
        category=line.category,
        days_by_contributor={
            contributor.id: line.days_of(contributor.id)
            for contributor in summary.contributors
            if line.days_of(contributor.id) > 0
        },
        days=line.days,
        own_days=line.own_days,
        own_days_by_contributor={
            contributor_id: days
            for contributor_id, days in line.days_by_contributor.items()
            if days > 0
        },
        share=summary.share_of(line.days),
        movement=line.movement,
        is_new=line.is_new,
        packages=[_line(package, summary) for package in line.packages],
    )
