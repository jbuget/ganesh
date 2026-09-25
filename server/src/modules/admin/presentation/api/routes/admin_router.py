"""Administration of the platform: read, never steered.

One route, and one door. Everything it answers is configured in the
environment — the model, the key, the mail server — so there is nothing here
to change and no route that would change it.
"""

from fastapi import APIRouter, Depends

from src.modules.admin.application.use_cases.read_platform import ReadPlatformUseCase
from src.modules.admin.domain.entities.platform import Wiring
from src.modules.admin.presentation.api.schemas.platform_schemas import (
    PlatformResponse,
    ServiceResponse,
)
from src.modules.admin.presentation.dependencies import get_read_platform_use_case
from src.modules.auth.presentation.dependencies import get_admin
from src.modules.users.domain.entities.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


def to_platform_response(wiring: Wiring) -> PlatformResponse:
    return PlatformResponse(
        environment=wiring.environment,
        door=wiring.door,
        services=[
            ServiceResponse(
                name=service.name,
                configured=service.configured,
                detail=service.detail,
            )
            for service in wiring.services
        ],
    )


@router.get("/platform", response_model=PlatformResponse, operation_id="readPlatform")
async def read_platform(
    _: User = Depends(get_admin),
    use_case: ReadPlatformUseCase = Depends(get_read_platform_use_case),
) -> PlatformResponse:
    """How Ganesh is wired. Administrators only."""
    return to_platform_response(await use_case.execute())
