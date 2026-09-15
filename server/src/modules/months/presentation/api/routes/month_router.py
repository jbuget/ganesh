"""Routes de validation et de reouverture des mois."""

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.auth.presentation.dependencies import (
    get_current_manager,
    get_current_user,
)
from src.modules.months.application.dtos.month_dto import (
    ReopenMonthCommand,
    ValidateMonthCommand,
)
from src.modules.months.application.use_cases.reopen_month import ReopenMonthUseCase
from src.modules.months.application.use_cases.validate_month import ValidateMonthUseCase
from src.modules.months.presentation.api.mappers.month_mapper import to_month_response
from src.modules.months.presentation.api.schemas.month_schemas import MonthResponse
from src.modules.months.presentation.dependencies import (
    get_reopen_month_use_case,
    get_validate_month_use_case,
)
from src.modules.users.domain.entities.user import User

router = APIRouter(prefix="/months", tags=["months"])


@router.post("/{mois}/validate", response_model=MonthResponse)
async def validate_month(
    mois: date,
    current_user: User = Depends(get_current_user),
    use_case: ValidateMonthUseCase = Depends(get_validate_month_use_case),
    session: AsyncSession = Depends(get_db),
) -> MonthResponse:
    """Verrouille son propre mois. La validation n'est pas delegable."""
    assert current_user.id is not None
    month = await use_case.execute(
        ValidateMonthCommand(
            actor_id=current_user.id, target_user_id=current_user.id, mois=mois
        )
    )
    await session.commit()
    return to_month_response(month)


@router.post("/{mois}/reopen", response_model=MonthResponse)
async def reopen_month(
    mois: date,
    user_id: int,
    manager: User = Depends(get_current_manager),
    use_case: ReopenMonthUseCase = Depends(get_reopen_month_use_case),
    session: AsyncSession = Depends(get_db),
) -> MonthResponse:
    """Rouvre le mois valide d'un collaborateur. Reserve aux managers."""
    assert manager.id is not None
    month = await use_case.execute(
        ReopenMonthCommand(actor_id=manager.id, target_user_id=user_id, mois=mois)
    )
    await session.commit()
    return to_month_response(month)
