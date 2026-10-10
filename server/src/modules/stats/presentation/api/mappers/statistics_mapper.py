"""Turns the dashboard of a window into what the screen reads."""

from src.modules.calendar.domain.entities.period import PeriodRange
from src.modules.stats.domain.entities.statistics import Statistics
from src.modules.stats.presentation.api.schemas.statistics_schemas import (
    AccountsResponse,
    ActivityDayResponse,
    AdoptionResponse,
    CategoryShareResponse,
    CoveragePointResponse,
    CoverageResponse,
    FreshnessResponse,
    IntakeResponse,
    KindReadingResponse,
    MissionShareResponse,
    MonthValidationResponse,
    NatureShareResponse,
    NotificationReadingResponse,
    PeriodResponse,
    RegistryResponse,
    StatisticsResponse,
    StatusShareResponse,
    SteeringResponse,
    StewardshipResponse,
    SurfaceActivityResponse,
    SurfaceUsageResponse,
    TeammateResponse,
    ThreadResponse,
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
            team=statistics.coverage_scope.team,
            people=statistics.coverage_scope.people,
        ),
        coverage_trend=[
            CoveragePointResponse(
                week_start=point.week_start,
                declared_days=point.declared_days,
                expected_days=point.expected_days,
                rate=point.rate,
            )
            for point in statistics.coverage_trend
        ],
        activity=[
            ActivityDayResponse(day=entry.day, gestures=entry.gestures)
            for entry in statistics.activity
        ],
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
            by_nature=[
                NatureShareResponse(
                    nature=nature, days=days, share=steering.share_of(days)
                )
                for nature, days in sorted(
                    steering.by_nature.items(), key=lambda item: -item[1]
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
            without_activity=statistics.registry.without_activity,
            unbudgeted=statistics.registry.unbudgeted,
            followed=statistics.registry.followed,
            published=statistics.registry.published,
        ),
        stewardship=StewardshipResponse(
            active_projects=statistics.stewardship.active_projects,
            without_lead=statistics.stewardship.without_lead,
            without_tech_lead=statistics.stewardship.without_tech_lead,
        ),
        thread=ThreadResponse(
            posted=statistics.thread.posted,
            answered=statistics.thread.answered,
            answer_rate=statistics.thread.answer_rate,
            followed=statistics.thread.followed,
            silent=statistics.thread.silent,
        ),
        notification_reading=NotificationReadingResponse(
            delivered=statistics.notification_reading.delivered,
            read=statistics.notification_reading.read,
            read_rate=statistics.notification_reading.read_rate,
            unread=statistics.notification_reading.unread,
            ignored=statistics.notification_reading.ignored,
            kinds=[
                KindReadingResponse(
                    kind=one.kind,
                    delivered=one.delivered,
                    read=one.read,
                    read_rate=one.read_rate,
                )
                for one in statistics.notification_reading.kinds
            ],
        ),
        accounts=AccountsResponse(
            guests=statistics.accounts.guests,
            teammates=statistics.accounts.teammates,
            managers=statistics.accounts.managers,
            admins=statistics.accounts.admins,
            never_signed_in=statistics.accounts.never_signed_in,
            reminders_daily=statistics.accounts.reminders_daily,
            reminders_weekly=statistics.accounts.reminders_weekly,
            reminders_never=statistics.accounts.reminders_never,
            reminder_rate=statistics.accounts.reminder_rate,
        ),
        intake=IntakeResponse(
            submitted=statistics.intake.submitted,
            accepted=statistics.intake.accepted,
            rejected=statistics.intake.rejected,
            deferred=statistics.intake.deferred,
            converted=statistics.intake.converted,
            waiting=statistics.intake.waiting,
            oldest_wait_days=statistics.intake.oldest_wait_days,
        ),
    )
