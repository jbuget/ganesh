"""Reads the figures of one window and assembles the dashboard."""

from src.modules.calendar.domain.entities.period import Period
from src.modules.calendar.domain.services.expectations import expected_days
from src.modules.projects.domain.entities.project import ProjectKind
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.requests.domain.entities.request import RequestState
from src.modules.stats.application.dtos.statistics_dto import StatisticsQuery
from src.modules.stats.domain.entities.statistics import (
    Adoption,
    Coverage,
    CoveragePoint,
    Freshness,
    Intake,
    MissionShare,
    MonthValidation,
    NotificationReading,
    Registry,
    Statistics,
    Steering,
    Stewardship,
    Teammate,
    Thread,
    age_in_days,
    ignored_before,
)
from src.modules.stats.domain.entities.surface_usage import SurfaceUsage, WindowReading
from src.modules.stats.domain.repositories.statistics_repository import (
    StatisticsRepository,
)
from src.modules.stats.domain.services.account_census import census_of
from src.modules.stats.domain.services.coverage_scope import (
    coverage_scope,
    measured_by_coverage,
)
from src.modules.stats.domain.services.declarers import who_declares
from src.modules.stats.domain.services.month_closing import closed_months_covered_by
from src.modules.stats.domain.services.surface_reading import (
    read_surfaces,
    surfaces_last_used,
)
from src.modules.stats.domain.services.trailing_weeks import trailing_weeks
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository

#: How many missions the steering block lists. A top that scrolls is a table,
#: not a reading.
TOP_MISSIONS = 5

#: How many weeks the coverage curve holds: a quarter, enough to tell a trend
#: from a holiday week, short enough to still be about the product as it is.
TREND_WEEKS = 12


class ComputeStatisticsUseCase:
    """Gathers what the screen shows for a window, and the one before it."""

    def __init__(self, users: UserRepository, statistics: StatisticsRepository) -> None:
        self._users = users
        self._statistics = statistics

    async def execute(self, query: StatisticsQuery) -> Statistics:
        period = Period.of(query.range_, query.today)
        previous = period.previous()
        accounts = await self._users.list_all()
        team = who_declares(accounts)
        measured = measured_by_coverage(team)

        return Statistics(
            period=period,
            coverage=await self._coverage(period, measured),
            previous_coverage=await self._coverage(previous, measured),
            coverage_scope=coverage_scope(measured),
            coverage_trend=await self._trend(query, measured),
            freshness=Freshness(delays=await self._statistics.entry_delays(period)),
            month_validation=await self._month_validation(period, query, team),
            adoption=await self._adoption(period, measured),
            surfaces=await self._surfaces(period, previous),
            steering=await self._steering(period),
            registry=await self._registry(period),
            intake=await self._intake(period, query),
            accounts=census_of(accounts),
            stewardship=await self._stewardship(),
            thread=await self._thread(period, query),
            notification_reading=await self._notification_reading(period, query),
        )

    async def _coverage(self, period: Period, measured: list[User]) -> Coverage:
        user_ids = [user.id for user in measured if user.id is not None]
        return Coverage(
            declared_days=await self._statistics.declared_days(period, user_ids),
            expected_days=expected_days(period, len(measured)),
        )

    async def _trend(
        self, query: StatisticsQuery, measured: list[User]
    ) -> list[CoveragePoint]:
        """One point per week, over the weeks leading up to today."""
        points: list[CoveragePoint] = []

        for week in trailing_weeks(query.today, TREND_WEEKS):
            coverage = await self._coverage(week, measured)
            points.append(
                CoveragePoint(
                    week_start=week.start,
                    declared_days=coverage.declared_days,
                    expected_days=coverage.expected_days,
                )
            )
        return points

    async def _month_validation(
        self, period: Period, query: StatisticsQuery, team: list[User]
    ) -> MonthValidation:
        months = closed_months_covered_by(period, query.today)
        user_ids = [user.id for user in team if user.id is not None]
        validated = (
            await self._statistics.validated_months(months, user_ids) if months else 0
        )
        return MonthValidation(validated=validated, due=len(months) * len(user_ids))

    async def _adoption(self, period: Period, measured: list[User]) -> Adoption:
        """Read over the team the coverage is measured on, and no other.

        The two figures answer to the same people: an adoption read over the
        whole company beside a coverage read over one team would not say whose
        habit is moving.
        """
        contributors = await self._statistics.contributor_ids(period)
        idle = [
            Teammate(id=user.id, display_name=user.label)
            for user in measured
            if user.id is not None and user.id not in contributors
        ]
        return Adoption(contributors=len(measured) - len(idle), idle=idle)

    async def _surfaces(self, period: Period, previous: Period) -> SurfaceUsage:
        """What each function of the product saw, and whether that is moving."""
        return read_surfaces(
            current=await self._reading(period),
            previous=await self._reading(previous),
            last_used=surfaces_last_used(
                gestures=await self._statistics.last_gestures(),
                others=await self._statistics.last_unlogged_use(),
            ),
        )

    async def _reading(self, period: Period) -> WindowReading:
        return WindowReading(
            traces=tuple(await self._statistics.surface_traces(period)),
            tallies=await self._statistics.unlogged_tallies(period),
        )

    async def _steering(self, period: Period) -> Steering:
        by_kind = await self._statistics.days_by_kind(period)
        off_project = by_kind.get(ProjectKind.OFF_PROJECT, 0.0)
        total = sum(by_kind.values())
        missions = await self._statistics.top_missions(period, TOP_MISSIONS)

        return Steering(
            project_days=total - off_project,
            off_project_days=off_project,
            by_status=await self._statistics.days_by_status(period),
            by_category=await self._statistics.days_by_category(period),
            by_nature=await self._statistics.days_by_nature(period),
            top_missions=[
                MissionShare(
                    project_id=project_id,
                    label=label,
                    days=days,
                    total_days=total,
                )
                for project_id, label, days in missions
            ],
        )

    async def _stewardship(self) -> Stewardship:
        return Stewardship(
            active_projects=await self._statistics.active_projects(),
            without_lead=await self._statistics.projects_without_role(ProjectRole.LEAD),
            without_tech_lead=await self._statistics.projects_without_role(
                ProjectRole.TECH_LEAD
            ),
        )

    async def _thread(self, period: Period, query: StatisticsQuery) -> Thread:
        last_news = await self._statistics.followed_last_news()
        return Thread(
            posted=await self._statistics.updates_posted(period),
            answered=await self._statistics.updates_answered(period),
            followed_news_ages=[
                None if day is None else age_in_days(day, query.today)
                for day in last_news
            ],
        )

    async def _notification_reading(
        self, period: Period, query: StatisticsQuery
    ) -> NotificationReading:
        return NotificationReading.of(
            await self._statistics.notification_reading(period),
            unread=await self._statistics.unread_notifications(),
            ignored=await self._statistics.unread_notifications(
                older_than=ignored_before(query.today)
            ),
        )

    async def _intake(self, period: Period, query: StatisticsQuery) -> Intake:
        decided = await self._statistics.requests_decided(period)
        waiting_since = await self._statistics.requests_waiting_since()

        return Intake(
            submitted=await self._statistics.requests_submitted(period),
            accepted=decided.get(RequestState.ACCEPTED, 0)
            + decided.get(RequestState.CONVERTED, 0),
            rejected=decided.get(RequestState.REJECTED, 0),
            deferred=decided.get(RequestState.DEFERRED, 0),
            converted=await self._statistics.requests_converted(period),
            waiting_days=[age_in_days(day, query.today) for day in waiting_since],
        )

    async def _registry(self, period: Period) -> Registry:
        return Registry(
            active_missions=await self._statistics.active_missions(),
            missions_with_time=await self._statistics.active_missions_with_time(period),
            created=await self._statistics.missions_created(period),
            without_activity=await self._statistics.missions_without_activity(),
            unbudgeted=await self._statistics.missions_unbudgeted(),
            followed=await self._statistics.followed_missions(),
            published=await self._statistics.published_missions(),
        )
