"""Turns the dashboard of a window into what the screen reads."""

from src.modules.calendar.domain.entities.period import PeriodRange
from src.modules.stats.domain.entities.statistics import Statistics
from src.modules.stats.presentation.api.schemas.statistics_schemas import (
    AdoptionResponse,
    CategoryShareResponse,
    CoverageResponse,
    FreshnessResponse,
    MissionShareResponse,
    MonthValidationResponse,
    PeriodResponse,
    RegistryResponse,
    StatisticsResponse,
    StatusShareResponse,
    SteeringResponse,
    SurfaceActivityResponse,
    SurfaceUsageResponse,
    TeammateResponse,
)


def to_statistics_response(
    statistics: Statistics, range_: PeriodRange
) -> StatisticsResponse:
    """Draws the figures out, heaviest first wherever a list is offered."""
    steering = statistics.steering

    return StatisticsResponse(
        period=PeriodResponse(
            range=range_,
            start=statistics.period.start,
            end=statistics.period.end,
            working_days=statistics.period.working_days,
        ),
        coverage=CoverageResponse(
            declared_days=statistics.coverage.declared_days,
            expected_days=statistics.coverage.expected_days,
            missing_days=statistics.coverage.missing_days,
            rate=statistics.coverage.rate,
            delta_in_points=statistics.coverage_delta_in_points,
        ),
        freshness=FreshnessResponse(
            entries=statistics.freshness.entries,
            median_delay=statistics.freshness.median_delay,
            day_to_day_share=statistics.freshness.day_to_day_share,
            late_share=statistics.freshness.late_share,
        ),
        month_validation=MonthValidationResponse(
            validated=statistics.month_validation.validated,
            due=statistics.month_validation.due,
            rate=statistics.month_validation.rate,
        ),
        adoption=AdoptionResponse(
            contributors=statistics.adoption.contributors,
            expected_contributors=statistics.adoption.expected_contributors,
            rate=statistics.adoption.rate,
            idle=[
                TeammateResponse(id=teammate.id, display_name=teammate.display_name)
                for teammate in statistics.adoption.idle
            ],
        ),
        surfaces=SurfaceUsageResponse(
            activities=[
                SurfaceActivityResponse(
                    surface=activity.surface,
                    people=activity.people,
                    gestures=activity.gestures,
                    delta_in_people=activity.delta_in_people,
                    is_idle=activity.is_idle,
                    last_used_on=activity.last_used_on,
                )
                # The order they come in is the order they are read in: it is
                # the domain's, and sorting here would lose it.
                for activity in statistics.surfaces.activities
            ],
            idle_count=statistics.surfaces.idle_count,
        ),
        steering=SteeringResponse(
            project_days=steering.project_days,
            off_project_days=steering.off_project_days,
            project_share=steering.project_share,
            by_status=[
                StatusShareResponse(
                    status=status, days=days, share=steering.share_of(days)
                )
                for status, days in sorted(
                    steering.by_status.items(), key=lambda item: -item[1]
                )
            ],
            by_category=[
                CategoryShareResponse(
                    category=category, days=days, share=steering.share_of(days)
                )
                for category, days in sorted(
                    steering.by_category.items(), key=lambda item: -item[1]
                )
            ],
            top_missions=[
                MissionShareResponse(
                    project_id=mission.project_id,
                    label=mission.label,
                    days=mission.days,
                    share=mission.share,
                )
                for mission in steering.top_missions
            ],
        ),
        registry=RegistryResponse(
            active_missions=statistics.registry.active_missions,
            missions_with_time=statistics.registry.missions_with_time,
            missions_without_time=statistics.registry.missions_without_time,
            usage_rate=statistics.registry.usage_rate,
            created=statistics.registry.created,
        ),
    )
