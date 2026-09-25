"""Wiring of the activity summary use case."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.activity_summary.application.use_cases.get_activity_summary import (
    GetActivitySummaryUseCase,
)
from src.modules.activity_summary.domain.repositories.activity_summary_repository import (
    ActivitySummaryRepository,
)
from src.modules.activity_summary.infrastructure.database.repositories.activity_summary_repository_impl import (
    SqlActivityRepository,
)
from src.modules.entries.presentation.dependencies import get_user_repository
from src.modules.users.domain.repositories.user_repository import UserRepository


def get_activity_repository(
    session: AsyncSession = Depends(get_db),
) -> ActivitySummaryRepository:
    return SqlActivityRepository(session)


def get_activity_summary_use_case(
    users: UserRepository = Depends(get_user_repository),
    activity: ActivitySummaryRepository = Depends(get_activity_repository),
) -> GetActivitySummaryUseCase:
    return GetActivitySummaryUseCase(users=users, activity=activity)
