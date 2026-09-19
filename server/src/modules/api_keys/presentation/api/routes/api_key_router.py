"""Routes of the service accounts.

These three are human routes: they depend on `get_current_user`, which refuses
API keys outright. A key can never manage keys.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.api_keys.application.dtos.api_key_dto import (
    CreateApiKeyCommand,
    RevokeApiKeyCommand,
    UpdateApiKeyCommand,
)
from src.modules.api_keys.application.use_cases.manage_api_keys import (
    CreateApiKeyUseCase,
    ListApiKeysUseCase,
    RevokeApiKeyUseCase,
    UpdateApiKeyUseCase,
)
from src.modules.api_keys.presentation.api.mappers.api_key_mapper import (
    to_api_key_response,
)
from src.modules.api_keys.presentation.api.schemas.api_key_schemas import (
    ApiKeyResponse,
    CreateApiKeyRequest,
    MintedApiKeyResponse,
    UpdateApiKeyRequest,
)
from src.modules.api_keys.presentation.dependencies import (
    get_create_api_key_use_case,
    get_list_api_keys_use_case,
    get_revoke_api_key_use_case,
    get_update_api_key_use_case,
)
from src.modules.auth.presentation.dependencies import (
    get_current_manager,
    get_current_user,
)
from src.modules.users.domain.entities.user import User

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.get("", response_model=list[ApiKeyResponse], operation_id="listApiKeys")
async def list_api_keys(
    _: User = Depends(get_current_user),
    use_case: ListApiKeysUseCase = Depends(get_list_api_keys_use_case),
) -> list[ApiKeyResponse]:
    """Every key, read by the whole team.

    Nothing here helps anyone use a key: the table carries the public half
    alone. Opening it is what puts eyes on a key nobody has called in months.
    """
    keys, people = await use_case.execute()
    now = datetime.now()
    return [to_api_key_response(key, people, now) for key in keys]


@router.post(
    "",
    response_model=MintedApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="createApiKey",
)
async def create_api_key(
    payload: CreateApiKeyRequest,
    manager: User = Depends(get_current_manager),
    use_case: CreateApiKeyUseCase = Depends(get_create_api_key_use_case),
    session: AsyncSession = Depends(get_db),
) -> MintedApiKeyResponse:
    """Mints a key and hands the token over. Once."""
    assert manager.id is not None
    minted = await use_case.execute(
        CreateApiKeyCommand(
            actor_id=manager.id,
            name=payload.name,
            owner_id=payload.owner_id,
            scopes=payload.scopes,
            expires_at=payload.expires_at,
        )
    )
    await session.commit()

    # The only two people a fresh key names, both already in hand: no second
    # trip to the database to answer.
    people = {user.id: user for user in (minted.owner, manager) if user.id is not None}
    return MintedApiKeyResponse(
        key=to_api_key_response(minted.key, people), token=minted.token
    )


@router.patch("/{key_id}", response_model=ApiKeyResponse, operation_id="updateApiKey")
async def update_api_key(
    key_id: int,
    payload: UpdateApiKeyRequest,
    manager: User = Depends(get_current_manager),
    use_case: UpdateApiKeyUseCase = Depends(get_update_api_key_use_case),
    list_use_case: ListApiKeysUseCase = Depends(get_list_api_keys_use_case),
    session: AsyncSession = Depends(get_db),
) -> ApiKeyResponse:
    """Corrects what a key is called and what it opens. Nothing else."""
    assert manager.id is not None
    key = await use_case.execute(
        UpdateApiKeyCommand(
            actor_id=manager.id,
            key_id=key_id,
            name=payload.name,
            scopes=payload.scopes,
        )
    )
    await session.commit()

    _, people = await list_use_case.execute()
    return to_api_key_response(key, people)


@router.delete(
    "/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="revokeApiKey",
)
async def revoke_api_key(
    key_id: int,
    manager: User = Depends(get_current_manager),
    use_case: RevokeApiKeyUseCase = Depends(get_revoke_api_key_use_case),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Cuts a key. Whatever uses it stops working immediately."""
    assert manager.id is not None
    await use_case.execute(RevokeApiKeyCommand(actor_id=manager.id, key_id=key_id))
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
