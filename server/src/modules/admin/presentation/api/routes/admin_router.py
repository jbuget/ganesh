"""Administration of the platform: read, never steered.

One route, and one door. Everything it answers is configured in the
environment — the model, the key, the mail server — so there is nothing here
to change and no route that would change it.
"""

from fastapi import APIRouter, Depends

from src.core.config import Settings, get_settings
from src.modules.admin.domain.entities.platform import Wiring, read_wiring
from src.modules.admin.presentation.api.schemas.platform_schemas import (
    PlatformResponse,
    ServiceResponse,
)
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
    settings: Settings = Depends(get_settings),
) -> PlatformResponse:
    """How Ganesh is wired. Administrators only."""
    return to_platform_response(
        read_wiring(
            environment=settings.environment,
            require_auth=settings.require_auth,
            auth_entra=settings.auth_entra,
            tenant_id=settings.azure_ad_tenant_id,
            gemini_api_key=settings.gemini_api_key,
            gemini_model=settings.gemini_model,
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            s3_bucket=settings.s3_bucket,
            s3_endpoint_url=settings.s3_endpoint_url,
        )
    )
