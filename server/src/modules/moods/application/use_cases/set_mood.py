"""Posts how a day felt."""

from datetime import date

from src.modules.moods.application.dtos.mood_dtos import SetMoodCommand
from src.modules.moods.domain.entities.mood import Mood
from src.modules.moods.domain.repositories.mood_repository import MoodRepository
from src.modules.moods.domain.services.mood_window import ensure_day_is_open
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)
from src.shared.utils import clock


class SetMoodUseCase:
    """Writes a mood, once the day is known to still accept one."""

    def __init__(self, users: UserRepository, moods: MoodRepository) -> None:
        self._users = users
        self._moods = moods

    async def execute(self, command: SetMoodCommand, today: date | None = None) -> Mood:
        author = await self._users.get_by_id(command.user_id)
        if author is None:
            raise EntityNotFoundError("The user cannot be found.")
        if not author.is_active:
            raise ForbiddenActionError("A deactivated user no longer posts a mood.")

        ensure_day_is_open(command.day, today or clock.today())

        previous = await self._moods.get(command.user_id, command.day)
        return await self._moods.upsert(
            Mood(
                id=previous.id if previous else None,
                user_id=command.user_id,
                day=command.day,
                level=command.level,
            )
        )
