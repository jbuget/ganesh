"""Routes de saisie du temps."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.entries.application.dtos.set_entry_dto import SetEntryCommand
from src.modules.entries.application.use_cases.get_month_grid import (
    GetMonthGridQuery,
    GetMonthGridUseCase,
)
from src.modules.entries.application.use_cases.set_entry import SetEntryUseCase
from src.modules.entries.presentation.api.mappers.entry_mapper import (
    to_entry_response,
    to_month_grid_response,
)
from src.modules.entries.presentation.api.schemas.entry_schemas import (
    EntryResponse,
    MonthGridResponse,
    SetEntryRequest,
)
from src.modules.entries.presentation.dependencies import (
    get_month_grid_use_case,
    get_set_entry_use_case,
)
from src.modules.users.domain.entities.user import User

router = APIRouter(prefix="/entries", tags=["entries"])


@router.get("/grid", response_model=MonthGridResponse)
async def get_month_grid(
    mois: date = Query(description="N'importe quel jour du mois demande"),
    user_id: int | None = Query(
        default=None,
        description="Collaborateur consulte. Par defaut, l'utilisateur courant.",
    ),
    current_user: User = Depends(get_current_user),
    use_case: GetMonthGridUseCase = Depends(get_month_grid_use_case),
) -> MonthGridResponse:
    """Retourne la matrice d'un mois. Chacun peut consulter le mois de chacun."""
    target_id = user_id or current_user.id
    assert target_id is not None
    grid = await use_case.execute(GetMonthGridQuery(user_id=target_id, mois=mois))
    return to_month_grid_response(grid)


@router.put("", response_model=EntryResponse)
async def set_entry(
    payload: SetEntryRequest,
    user_id: int | None = Query(
        default=None,
        description="Collaborateur dont le mois est modifie.",
    ),
    current_user: User = Depends(get_current_user),
    use_case: SetEntryUseCase = Depends(get_set_entry_use_case),
    session: AsyncSession = Depends(get_db),
) -> EntryResponse:
    """Enregistre une saisie, pour soi ou pour un collegue."""
    assert current_user.id is not None
    entry = await use_case.execute(
        SetEntryCommand(
            actor_id=current_user.id,
            target_user_id=user_id or current_user.id,
            project_id=payload.project_id,
            jour=payload.jour,
            valeur=payload.valeur,
        )
    )
    await session.commit()
    return to_entry_response(entry)
