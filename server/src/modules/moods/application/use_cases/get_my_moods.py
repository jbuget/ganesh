"""What one may still answer for, and what one has already said."""

from datetime import date

from src.modules.moods.application.dtos.mood_dtos import OpenDay
from src.modules.moods.domain.repositories.mood_repository import MoodRepository
from src.modules.moods.domain.services.mood_window import open_days
from src.shared.utils import clock


class GetMyMoodsUseCase:
    """The open days of a teammate, filled in with what they posted."""

    def __init__(self, moods: MoodRepository) -> None:
        self._moods = moods

    async def execute(self, user_id: int, today: date | None = None) -> list[OpenDay]:
        days = open_days(today or clock.today())
        posted = {
            mood.day: mood.level
            for mood in await self._moods.list_for_user_between(
                user_id, min(days), max(days)
            )
        }
        return [OpenDay(day=day, level=posted.get(day)) for day in days]
