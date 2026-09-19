"""Mood routes.

Everyone reads the team's morale, and nobody posts for anybody else. Both are
deliberate: the screen is a mirror the team holds up to itself, not a measure
taken of it.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.moods.application.dtos.mood_dtos import SetMoodCommand
from src.modules.moods.application.use_cases.get_my_moods import GetMyMoodsUseCase
from src.modules.moods.application.use_cases.get_team_moods import GetTeamMoodsUseCase
from src.modules.moods.application.use_cases.set_mood import SetMoodUseCase
from src.modules.moods.presentation.api.mappers.mood_mapper import (
    to_mood_response,
    to_my_moods_response,
    to_team_moods_response,
)
from src.modules.moods.presentation.api.schemas.mood_schemas import (
    MoodResponse,
    MyMoodsResponse,
    SetMoodRequest,
    TeamMoodsResponse,
)
from src.modules.moods.presentation.dependencies import (
    get_my_moods_use_case,
    get_set_mood_use_case,
    get_team_moods_use_case,
)
from src.modules.users.domain.entities.user import User

router = APIRouter(prefix="/moods", tags=["moods"])


@router.get("/me", response_model=MyMoodsResponse, operation_id="getMyMoods")
async def get_my_moods(
    current_user: User = Depends(get_current_user),
    use_case: GetMyMoodsUseCase = Depends(get_my_moods_use_case),
) -> MyMoodsResponse:
    """The days one may still answer for, and what one already said of them."""
    assert current_user.id is not None
    return to_my_moods_response(await use_case.execute(current_user.id))


@router.put("", response_model=MoodResponse, operation_id="setMood")
async def set_mood(
    payload: SetMoodRequest,
    current_user: User = Depends(get_current_user),
    use_case: SetMoodUseCase = Depends(get_set_mood_use_case),
    session: AsyncSession = Depends(get_db),
) -> MoodResponse:
    """Posts how a day felt, or changes what was posted."""
    assert current_user.id is not None
    mood = await use_case.execute(
        SetMoodCommand(user_id=current_user.id, day=payload.day, level=payload.level)
    )
    await session.commit()
    return to_mood_response(mood)


@router.get("/team", response_model=TeamMoodsResponse, operation_id="getTeamMoods")
async def get_team_moods(
    _: User = Depends(get_current_user),
    use_case: GetTeamMoodsUseCase = Depends(get_team_moods_use_case),
) -> TeamMoodsResponse:
    """The team's morale over the last fortnight. Everyone reads it."""
    return to_team_moods_response(await use_case.execute())
