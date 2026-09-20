"""Time entry routes."""

from datetime import date

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.api_keys.presentation.dependencies import Caller, open_to_machines
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.entries.application.dtos.set_entry_dto import (
    AddMissionCommand,
    ClearEntryCommand,
    RemoveMissionCommand,
    SetEntryCommand,
)
from src.modules.entries.application.use_cases.add_mission_to_month import (
    AddMissionToMonthUseCase,
)
from src.modules.entries.application.use_cases.clear_entry import ClearEntryUseCase
from src.modules.entries.application.use_cases.export_entries import (
    ExportEntriesUseCase,
)
from src.modules.entries.application.use_cases.get_month_grid import (
    GetMonthGridQuery,
    GetMonthGridUseCase,
)
from src.modules.entries.application.use_cases.remove_mission_from_month import (
    RemoveMissionFromMonthUseCase,
)
from src.modules.entries.application.use_cases.set_entry import SetEntryUseCase
from src.modules.entries.presentation.api.mappers.entry_mapper import (
    to_entry_response,
    to_month_grid_response,
)
from src.modules.entries.presentation.api.schemas.entry_schemas import (
    AddMissionRequest,
    EntriesExportResponse,
    EntryResponse,
    ExportedEntryResponse,
    MonthGridResponse,
    SetEntryRequest,
)
from src.modules.entries.presentation.dependencies import (
    get_add_mission_use_case,
    get_clear_entry_use_case,
    get_export_entries_use_case,
    get_month_grid_use_case,
    get_remove_mission_use_case,
    get_set_entry_use_case,
)
from src.modules.users.domain.entities.user import User

router = APIRouter(prefix="/entries", tags=["entries"])

#: The register as a machine reads it: payroll, invoicing, a dashboard outside
#: Ganesh. Reading only. Writing time is left human on purpose — a validated
#: month, a day that is not a working one and a total that may not exceed one
#: are rules a person is told about on screen and argues with; a machine would
#: only be told « 422 ».
entries_reader = open_to_machines(ApiKeyScope.ENTRIES_READ)


@router.get("/grid", response_model=MonthGridResponse, operation_id="getMonthGrid")
async def get_month_grid(
    month: date = Query(description="Any day of the month asked for"),
    user_id: int | None = Query(
        default=None,
        description="Teammate being looked at. Defaults to the current user.",
    ),
    current_user: User = Depends(get_current_user),
    use_case: GetMonthGridUseCase = Depends(get_month_grid_use_case),
) -> MonthGridResponse:
    """Returns a month's grid. Anyone may look at anyone's month."""
    target_id = user_id or current_user.id
    assert target_id is not None
    grid = await use_case.execute(GetMonthGridQuery(user_id=target_id, month=month))
    return to_month_grid_response(grid)


@router.get(
    "/export", response_model=EntriesExportResponse, operation_id="exportEntries"
)
async def export_entries(
    from_day: date = Query(description="First day of the window, included"),
    to_day: date = Query(description="Last day of the window, included"),
    _: Caller = Depends(entries_reader),
    use_case: ExportEntriesUseCase = Depends(get_export_entries_use_case),
) -> EntriesExportResponse:
    """Everything declared between two days, whoever declared it.

    Declared and forecast alike, as the grid holds them: what is posted ahead
    is part of the register, and an export that told them apart would be
    reading the days rather than handing them over.

    Declared **on** the window, not declared *during* it: a day entered late
    comes out under the day it is about. Which is what a register is for, and
    why a pull done twice over the same window can differ.
    """
    entries = await use_case.execute(from_day, to_day)
    return EntriesExportResponse(
        from_day=from_day,
        to_day=to_day,
        entries=[
            ExportedEntryResponse(
                day=entry.day,
                value=entry.value,
                status_at_entry=entry.status_at_entry,
                user_id=entry.user_id,
                user_label=entry.user_label,
                project_id=entry.project_id,
                project_label=entry.project_label,
            )
            for entry in entries
        ],
    )


@router.put("", response_model=EntryResponse, operation_id="setEntry")
async def set_entry(
    payload: SetEntryRequest,
    user_id: int | None = Query(
        default=None,
        description="Teammate whose month is changed.",
    ),
    current_user: User = Depends(get_current_user),
    use_case: SetEntryUseCase = Depends(get_set_entry_use_case),
    session: AsyncSession = Depends(get_db),
) -> EntryResponse:
    """Records an entry, for oneself or for a colleague."""
    assert current_user.id is not None
    entry = await use_case.execute(
        SetEntryCommand(
            actor_id=current_user.id,
            target_user_id=user_id or current_user.id,
            project_id=payload.project_id,
            day=payload.day,
            value=payload.value,
        )
    )
    await session.commit()
    return to_entry_response(entry)


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="clearEntry",
)
async def clear_entry(
    project_id: int,
    day: date,
    user_id: int | None = Query(
        default=None, description="Teammate whose month is changed."
    ),
    current_user: User = Depends(get_current_user),
    use_case: ClearEntryUseCase = Depends(get_clear_entry_use_case),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Removes an entry, for oneself or for a colleague."""
    assert current_user.id is not None
    await use_case.execute(
        ClearEntryCommand(
            actor_id=current_user.id,
            target_user_id=user_id or current_user.id,
            project_id=project_id,
            day=day,
        )
    )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/mission",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="addMissionToMonth",
)
async def add_mission_to_month(
    payload: AddMissionRequest,
    user_id: int | None = Query(
        default=None, description="Teammate whose month is changed."
    ),
    current_user: User = Depends(get_current_user),
    use_case: AddMissionToMonthUseCase = Depends(get_add_mission_use_case),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Puts a mission on a month, with no time on it yet."""
    assert current_user.id is not None
    await use_case.execute(
        AddMissionCommand(
            actor_id=current_user.id,
            target_user_id=user_id or current_user.id,
            project_id=payload.project_id,
            month=payload.month,
        )
    )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/mission",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="removeMissionFromMonth",
)
async def remove_mission_from_month(
    project_id: int,
    month: date = Query(description="Any day of the month aimed at"),
    user_id: int | None = Query(
        default=None, description="Teammate whose month is changed."
    ),
    current_user: User = Depends(get_current_user),
    use_case: RemoveMissionFromMonthUseCase = Depends(get_remove_mission_use_case),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Removes a mission from a month, with the time it carries."""
    assert current_user.id is not None
    await use_case.execute(
        RemoveMissionCommand(
            actor_id=current_user.id,
            target_user_id=user_id or current_user.id,
            project_id=project_id,
            month=month,
        )
    )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
