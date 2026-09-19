"""Wiring of the mood use cases."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.moods.application.use_cases.get_my_moods import GetMyMoodsUseCase
from src.modules.moods.application.use_cases.get_team_moods import GetTeamMoodsUseCase
from src.modules.moods.application.use_cases.set_mood import SetMoodUseCase
from src.modules.moods.domain.repositories.mood_repository import MoodRepository
from src.modules.moods.infrastructure.database.repositories.mood_repository_impl import (
    SqlMoodRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)


def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return SqlUserRepository(session)


def get_mood_repository(session: AsyncSession = Depends(get_db)) -> MoodRepository:
    return SqlMoodRepository(session)


def get_set_mood_use_case(
    users: UserRepository = Depends(get_user_repository),
    moods: MoodRepository = Depends(get_mood_repository),
) -> SetMoodUseCase:
    return SetMoodUseCase(users=users, moods=moods)


def get_my_moods_use_case(
    moods: MoodRepository = Depends(get_mood_repository),
) -> GetMyMoodsUseCase:
    return GetMyMoodsUseCase(moods=moods)


def get_team_moods_use_case(
    users: UserRepository = Depends(get_user_repository),
    moods: MoodRepository = Depends(get_mood_repository),
) -> GetTeamMoodsUseCase:
    return GetTeamMoodsUseCase(users=users, moods=moods)
