"""Teammate routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.api_keys.presentation.dependencies import Caller, open_to_machines
from src.modules.auth.presentation.dependencies import (
    get_current_manager,
    get_current_user,
)
from src.modules.users.application.dtos.user_dto import (
    ChangeRoleCommand,
    SetUserActiveCommand,
    UpdateUserIdentityCommand,
)
from src.modules.users.application.dtos.user_record_dto import GetUserRecordQuery
from src.modules.users.application.use_cases.change_user_role import (
    ChangeUserRoleUseCase,
)
from src.modules.users.application.use_cases.get_user_record import GetUserRecordUseCase
from src.modules.users.application.use_cases.list_users import ListUsersUseCase
from src.modules.users.application.use_cases.set_user_active import SetUserActiveUseCase
from src.modules.users.application.use_cases.update_user_identity import (
    UpdateUserIdentityUseCase,
)
from src.modules.users.domain.entities.user import User
from src.modules.users.presentation.api.mappers.user_mapper import to_user_response
from src.modules.users.presentation.api.mappers.user_record_mapper import (
    to_user_record_response,
)
from src.modules.users.presentation.api.schemas.user_record_schemas import (
    UserRecordResponse,
)
from src.modules.users.presentation.api.schemas.user_schemas import (
    ChangeRoleRequest,
    SetActiveRequest,
    UpdateUserIdentityRequest,
    UserResponse,
)
from src.modules.users.presentation.dependencies import (
    get_change_role_use_case,
    get_list_users_use_case,
    get_set_user_active_use_case,
    get_update_user_identity_use_case,
    get_user_record_use_case,
)

router = APIRouter(prefix="/users", tags=["users"])

#: The directory a machine may read. Reading only: a role and an activation are
#: a manager's gestures, and a key carries no role — opening them to one would
#: hand a machine the very power the design refuses it.
directory_reader = open_to_machines(ApiKeyScope.USERS_READ)


@router.get("/me", response_model=UserResponse, operation_id="getMe")
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """The current user, as provisioned from Entra."""
    return to_user_response(current_user)


@router.get("", response_model=list[UserResponse], operation_id="listUsers")
async def list_users(
    include_inactive: bool = Query(default=False),
    _: Caller = Depends(directory_reader),
    use_case: ListUsersUseCase = Depends(get_list_users_use_case),
) -> list[UserResponse]:
    """Lists the teammates. Anyone may look at anyone's month."""
    users = await use_case.execute(include_inactive=include_inactive)
    return [to_user_response(user) for user in users]


@router.get(
    "/{user_id}/record",
    response_model=UserRecordResponse,
    operation_id="getUserRecord",
)
async def get_user_record(
    user_id: int,
    _: User = Depends(get_current_user),
    use_case: GetUserRecordUseCase = Depends(get_user_record_use_case),
) -> UserRecordResponse:
    """What the register holds on a teammate. Open to the whole team.

    Anyone may look at anyone's month, so anyone may read what leads to it:
    the missions somebody is attached to, the time they declared lately, and
    where their months stand. Nothing here is a manager's secret — changing a
    role or an access still is.
    """
    record = await use_case.execute(GetUserRecordQuery(user_id=user_id))
    return to_user_record_response(record)


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


@router.patch(
    "/{user_id}/identity",
    response_model=UserResponse,
    operation_id="updateUserIdentity",
)
async def update_identity(
    user_id: int,
    payload: UpdateUserIdentityRequest,
    manager: User = Depends(get_current_manager),
    use_case: UpdateUserIdentityUseCase = Depends(get_update_user_identity_use_case),
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Gives away who a teammate is, and how one reaches them. Managers only."""
    assert manager.id is not None
    user = await use_case.execute(
        UpdateUserIdentityCommand(
            actor_id=manager.id,
            target_user_id=user_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            department=payload.department,
            github_username=payload.github_username,
        )
    )
    await session.commit()
    return to_user_response(user)
