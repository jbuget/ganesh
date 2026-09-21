"""Reads the figures of one window and assembles the dashboard."""

from src.modules.calendar.domain.entities.period import Period
from src.modules.calendar.domain.services.expectations import expected_days
from src.modules.projects.domain.entities.project import ProjectKind
from src.modules.stats.application.dtos.statistics_dto import StatisticsQuery
from src.modules.stats.domain.entities.statistics import (
    Adoption,
    Coverage,
    Freshness,
    MissionShare,
    MonthValidation,
    Registry,
    Statistics,
    Steering,
    Teammate,
)
from src.modules.stats.domain.entities.surface_usage import SurfaceUsage, WindowReading
from src.modules.stats.domain.repositories.statistics_repository import (
    StatisticsRepository,
)
from src.modules.stats.domain.services.month_closing import closed_months_covered_by
from src.modules.stats.domain.services.surface_reading import (
    read_surfaces,
    surfaces_last_used,
)
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository

#: How many missions the steering block lists. A top that scrolls is a table,
#: not a reading.
TOP_MISSIONS = 5


class ComputeStatisticsUseCase:
    """Gathers what the screen shows for a window, and the one before it."""

    def __init__(self, users: UserRepository, statistics: StatisticsRepository) -> None:
        self._users = users
        self._statistics = statistics

    async def execute(self, query: StatisticsQuery) -> Statistics:
        period = Period.of(query.range_, query.today)
        previous = period.previous()
        team = await self._users.list_all()

        coverage = await self._coverage(period, len(team))
        previous_coverage = await self._coverage(previous, len(team))

        return Statistics(
            period=period,
            coverage=coverage,
            previous_coverage=previous_coverage,
            freshness=Freshness(delays=await self._statistics.entry_delays(period)),
            month_validation=await self._month_validation(period, query, team),
            adoption=await self._adoption(period, team),
            surfaces=await self._surfaces(period, previous),
            steering=await self._steering(period),
            registry=await self._registry(period),
        )

    async def _coverage(self, period: Period, teammates: int) -> Coverage:
        return Coverage(
            declared_days=await self._statistics.declared_days(period),
            expected_days=expected_days(period, teammates),
        )

    async def _month_validation(
        self, period: Period, query: StatisticsQuery, team: list[User]
    ) -> MonthValidation:
        months = closed_months_covered_by(period, query.today)
        user_ids = [user.id for user in team if user.id is not None]
        validated = (
            await self._statistics.validated_months(months, user_ids) if months else 0
        )
        return MonthValidation(validated=validated, due=len(months) * len(user_ids))

    async def _adoption(self, period: Period, team: list[User]) -> Adoption:
        contributors = await self._statistics.contributor_ids(period)
        idle = [
            Teammate(id=user.id, display_name=user.label)
            for user in team
            if user.id is not None and user.id not in contributors
        ]
        return Adoption(contributors=len(team) - len(idle), idle=idle)

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

    async def _registry(self, period: Period) -> Registry:
        return Registry(
            active_missions=await self._statistics.active_missions(),
            missions_with_time=await self._statistics.active_missions_with_time(period),
            created=await self._statistics.missions_created(period),
        )
