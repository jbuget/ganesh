"""The team's morale over the last fortnight."""

from datetime import date

from src.modules.moods.application.dtos.mood_dtos import TeamMoods
from src.modules.moods.domain.repositories.mood_repository import MoodRepository
from src.modules.moods.domain.services.mood_report import build_report
from src.modules.moods.domain.services.mood_window import DEFAULT_SPAN, window_days
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.utils import clock


class GetTeamMoodsUseCase:
    """Reads the window the team screen draws."""

    def __init__(self, users: UserRepository, moods: MoodRepository) -> None:
        self._users = users
        self._moods = moods

    async def execute(
        self, today: date | None = None, span: int = DEFAULT_SPAN
    ) -> TeamMoods:
        days = window_days(today or clock.today(), span=span)

        # Deactivated teammates come along: they posted while they were here,
        # and dropping them would leave moods no name could be put on.
        people = await self._users.list_all(include_inactive=True)
        moods = await self._moods.list_between(min(days), max(days))

        # Who the window is about: whoever may answer today, plus whoever
        # answered during it. Counting the active alone made a day read « 8 / 7 »
        # as soon as someone who has since left had posted — a share above its
        # whole says the denominator is the wrong one.
        answered = {mood.user_id for mood in moods}
        headcount = sum(
            1 for person in people if person.is_active or person.id in answered
        )

        return TeamMoods(
            report=build_report(days, moods, headcount=headcount), people=people
        )
