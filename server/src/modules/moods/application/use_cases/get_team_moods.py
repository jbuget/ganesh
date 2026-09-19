"""The team's morale over the last fortnight."""

from datetime import date

from src.modules.moods.application.dtos.mood_dtos import TeamMoods
from src.modules.moods.domain.repositories.mood_repository import MoodRepository
from src.modules.moods.domain.services.mood_report import build_report
from src.modules.moods.domain.services.mood_window import DEFAULT_SPAN, window_days
from src.modules.users.domain.repositories.user_repository import UserRepository


class GetTeamMoodsUseCase:
    """Reads the window the team screen draws."""

    def __init__(self, users: UserRepository, moods: MoodRepository) -> None:
        self._users = users
        self._moods = moods

    async def execute(
        self, today: date | None = None, span: int = DEFAULT_SPAN
    ) -> TeamMoods:
        days = window_days(today or date.today(), span=span)

        # Deactivated teammates come along: they posted while they were here,
        # and dropping them would leave moods no name could be put on. They
        # are left out of the headcount alone, which counts who could answer
        # today.
        people = await self._users.list_all(include_inactive=True)
        headcount = sum(1 for person in people if person.is_active)

        moods = await self._moods.list_between(min(days), max(days))
        return TeamMoods(
            report=build_report(days, moods, headcount=headcount), people=people
        )
