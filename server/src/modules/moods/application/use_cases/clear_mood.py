"""Takes back the mood posted on a day."""

from datetime import date

from src.modules.moods.application.dtos.mood_dtos import ClearMoodCommand
from src.modules.moods.domain.repositories.mood_repository import MoodRepository
from src.modules.moods.domain.services.mood_window import ensure_day_is_open
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)
from src.shared.utils import clock


class ClearMoodUseCase:
    """Removes a mood, while the day it belongs to is still open.

    The window governs both ways: what one can no longer write, one can no
    longer unwrite. A fortnight that could be emptied after the fact would
    make the record say whatever its author last decided.
    """

    def __init__(self, users: UserRepository, moods: MoodRepository) -> None:
        self._users = users
        self._moods = moods

    async def execute(
        self, command: ClearMoodCommand, today: date | None = None
    ) -> None:
        author = await self._users.get_by_id(command.user_id)
        if author is None:
            raise EntityNotFoundError("The user cannot be found.")
        if not author.is_active:
            raise ForbiddenActionError("A deactivated user no longer posts a mood.")

        ensure_day_is_open(command.day, today or clock.today())

        # A day carrying no mood is left alone rather than reported: taking
        # back what was never posted is what a second click on the same face
        # does, and it is not a mistake.
        await self._moods.delete(command.user_id, command.day)
