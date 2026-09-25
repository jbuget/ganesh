"""Reads one window and assembles the matrix the screen draws."""

from src.modules.activity_summary.application.dtos.activity_summary_dto import (
    ActivitySummaryQuery,
)
from src.modules.activity_summary.domain.entities.activity_summary import (
    ActivitySummary,
)
from src.modules.activity_summary.domain.repositories.activity_summary_repository import (
    ActivitySummaryRepository,
)
from src.modules.activity_summary.domain.services.summarising import Teammate, summarise
from src.modules.calendar.domain.entities.period import Period
from src.modules.users.domain.repositories.user_repository import UserRepository


class GetActivitySummaryUseCase:
    """Gathers what the screen shows for a window, and the one before it."""

    def __init__(
        self, users: UserRepository, activity: ActivitySummaryRepository
    ) -> None:
        self._users = users
        self._activity = activity

    async def execute(self, query: ActivitySummaryQuery) -> ActivitySummary:
        period = Period.of(query.range_, query.today)

        return summarise(
            period=period,
            team=[
                Teammate(id=user.id, display_name=user.label)
                for user in await self._users.list_all()
                if user.id is not None
            ],
            missions=await self._activity.missions_touched(period),
            declared=await self._activity.declared_days(period),
            # The window before, so that every line can say what it moved.
            previous=await self._activity.days_by_mission(period.previous()),
        )
