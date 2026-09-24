"""Routes to validate and reopen months."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.audit_logs.application.use_cases.list_month_audit_log import (
    ListMonthAuditLogUseCase,
)
from src.modules.audit_logs.presentation.api.mappers.audit_log_mapper import (
    to_audit_log_page_response,
)
from src.modules.audit_logs.presentation.api.schemas.audit_log_schemas import (
    AuditLogPageResponse,
)
from src.modules.audit_logs.presentation.dependencies import (
    get_month_audit_log_use_case,
)
from src.modules.auth.presentation.dependencies import (
    get_contributor,
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


@router.post(
    "/{month}/validate", response_model=MonthResponse, operation_id="validateMonth"
)
async def validate_month(
    month: date,
    current_user: User = Depends(get_contributor),
    use_case: ValidateMonthUseCase = Depends(get_validate_month_use_case),
    session: AsyncSession = Depends(get_db),
) -> MonthResponse:
    """Locks one's own month. Validation cannot be delegated."""
    assert current_user.id is not None
    validated = await use_case.execute(
        ValidateMonthCommand(
            actor_id=current_user.id, target_user_id=current_user.id, month=month
        )
    )
    await session.commit()
    return to_month_response(validated)


@router.post(
    "/{month}/reopen", response_model=MonthResponse, operation_id="reopenMonth"
)
async def reopen_month(
    month: date,
    user_id: int,
    manager: User = Depends(get_current_manager),
    use_case: ReopenMonthUseCase = Depends(get_reopen_month_use_case),
    session: AsyncSession = Depends(get_db),
) -> MonthResponse:
    """Reopens a teammate's validated month. Managers only."""
    assert manager.id is not None
    reopened = await use_case.execute(
        ReopenMonthCommand(actor_id=manager.id, target_user_id=user_id, month=month)
    )
    await session.commit()
    return to_month_response(reopened)


@router.get(
    "/{month}/audit",
    response_model=AuditLogPageResponse,
    operation_id="listMonthAuditLog",
)
async def list_month_audit_log(
    month: date,
    user_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(get_current_user),
    use_case: ListMonthAuditLogUseCase = Depends(get_month_audit_log_use_case),
) -> AuditLogPageResponse:
    """Everything that happened to that month, most recent first.

    Read by the whole team rather than by its owner alone: anyone may edit a
    colleague's open month, and that freedom only holds up if the trace it
    leaves can be read back by anyone too.
    """
    return to_audit_log_page_response(
        await use_case.execute(
            target_user_id=user_id, month=month, limit=limit, offset=offset
        )
    )
