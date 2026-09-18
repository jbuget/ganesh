"""Teammate routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.auth.presentation.dependencies import (
    get_current_manager,
    get_current_user,
)
from src.modules.users.application.dtos.user_dto import (
    ChangeRoleCommand,
    SetUserActiveCommand,
)
from src.modules.users.application.use_cases.change_user_role import (
    ChangeUserRoleUseCase,
)
from src.modules.users.application.use_cases.list_users import ListUsersUseCase
from src.modules.users.application.use_cases.set_user_active import SetUserActiveUseCase
from src.modules.users.domain.entities.user import User
from src.modules.users.presentation.api.mappers.user_mapper import to_user_response
from src.modules.users.presentation.api.schemas.user_schemas import (
    ChangeRoleRequest,
    SetActiveRequest,
    UserResponse,
)
from src.modules.users.presentation.dependencies import (
    get_change_role_use_case,
    get_list_users_use_case,
    get_set_user_active_use_case,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse, operation_id="getMe")
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """L'utilisateur courant, tel que provisionne depuis Entra."""
    return to_user_response(current_user)


@router.get("", response_model=list[UserResponse], operation_id="listUsers")
async def list_users(
    include_inactive: bool = Query(default=False),
    _: User = Depends(get_current_user),
    use_case: ListUsersUseCase = Depends(get_list_users_use_case),
) -> list[UserResponse]:
    """Lists the teammates. Anyone may look at anyone's month."""
    users = await use_case.execute(include_inactive=include_inactive)
    return [to_user_response(user) for user in users]


@router.patch(
    "/{user_id}/role", response_model=UserResponse, operation_id="changeUserRole"
)
async def change_role(
    user_id: int,
    payload: ChangeRoleRequest,
    manager: User = Depends(get_current_manager),
    use_case: ChangeUserRoleUseCase = Depends(get_change_role_use_case),
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Changes a teammate's role. Managers only."""
    assert manager.id is not None
    user = await use_case.execute(
        ChangeRoleCommand(
            actor_id=manager.id, target_user_id=user_id, role=payload.role
        )
    )
    await session.commit()
    return to_user_response(user)


@router.patch(
    "/{user_id}/actif", response_model=UserResponse, operation_id="setUserActive"
)
async def set_active(
    user_id: int,
    payload: SetActiveRequest,
    manager: User = Depends(get_current_manager),
    use_case: SetUserActiveUseCase = Depends(get_set_user_active_use_case),
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Cuts off or restores a teammate's access. Managers only."""
    assert manager.id is not None
    user = await use_case.execute(
        SetUserActiveCommand(
            actor_id=manager.id, target_user_id=user_id, is_active=payload.is_active
        )
    )
    await session.commit()
    return to_user_response(user)
