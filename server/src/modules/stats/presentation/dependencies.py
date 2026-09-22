"""Wiring of the statistics use case."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.entries.presentation.dependencies import get_user_repository
from src.modules.stats.application.use_cases.compute_statistics import (
    ComputeStatisticsUseCase,
)
from src.modules.stats.domain.repositories.statistics_repository import (
    StatisticsRepository,
)
from src.modules.stats.infrastructure.database.repositories.statistics_repository_impl import (
    SqlStatisticsRepository,
)
from src.modules.users.domain.repositories.rhythm_repository import RhythmRepository
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.modules.users.presentation.dependencies import get_rhythm_repository


def get_statistics_repository(
    session: AsyncSession = Depends(get_db),
) -> StatisticsRepository:
    return SqlStatisticsRepository(session)


def get_compute_statistics_use_case(
    users: UserRepository = Depends(get_user_repository),
    statistics: StatisticsRepository = Depends(get_statistics_repository),
    rhythms: RhythmRepository = Depends(get_rhythm_repository),
) -> ComputeStatisticsUseCase:
    return ComputeStatisticsUseCase(users=users, statistics=statistics, rhythms=rhythms)
