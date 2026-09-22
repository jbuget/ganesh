"""Reads one window and assembles the matrix the screen draws."""

from src.modules.activity.application.dtos.activity_dto import ActivityQuery
from src.modules.activity.domain.entities.activity import ActivitySummary
from src.modules.activity.domain.repositories.activity_repository import (
    ActivityRepository,
)
from src.modules.activity.domain.services.summarising import Teammate, summarise
from src.modules.calendar.domain.entities.period import Period
from src.modules.users.domain.repositories.rhythm_repository import RhythmRepository
from src.modules.users.domain.repositories.user_repository import UserRepository


class GetActivitySummaryUseCase:
    """Gathers what the screen shows for a window, and the one before it."""

    def __init__(
        self,
        users: UserRepository,
        activity: ActivityRepository,
        rhythms: RhythmRepository,
    ) -> None:
        self._users = users
        self._activity = activity
        self._rhythms = rhythms

    async def execute(self, query: ActivityQuery) -> ActivitySummary:
        period = Period.of(query.range_, query.today)

        team = [user for user in await self._users.list_all() if user.id is not None]
        # Everyone's rhythms in one go: a coverage computed a query per column
        # is the same figure, read as many times slower.
        histories = await self._rhythms.histories_of(
            [user.id for user in team if user.id is not None]
        )

        return summarise(
            period=period,
            team=[
                Teammate(
                    id=user.id,
                    display_name=user.label,
                    rhythm=histories[user.id],
                )
                for user in team
                if user.id is not None
            ],
            missions=await self._activity.missions_touched(period),
            declared=await self._activity.declared_days(period),
            # The window before, so that every line can say what it moved.
            previous=await self._activity.days_by_mission(period.previous()),
        )
