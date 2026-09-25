"""Wiring of the administration use cases."""

from fastapi import Depends

from src.core.config import Settings, get_settings
from src.modules.admin.application.dtos.platform_dto import PlatformSettings
from src.modules.admin.application.use_cases.read_platform import ReadPlatformUseCase


def get_read_platform_use_case(
    settings: Settings = Depends(get_settings),
) -> ReadPlatformUseCase:
    """Unpacks the environment here, and nowhere deeper.

    `has_gemini_key` rather than the key: the reading says a service is wired,
    and a secret that travelled one layer further than it had to is a secret
    one day handed back through a screen.
    """
    return ReadPlatformUseCase(
        PlatformSettings(
            environment=settings.environment,
            require_auth=settings.require_auth,
            auth_entra=settings.auth_entra,
            tenant_id=settings.azure_ad_tenant_id,
            has_gemini_key=bool(settings.gemini_api_key),
            gemini_model=settings.gemini_model,
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            s3_bucket=settings.s3_bucket,
            s3_endpoint_url=settings.s3_endpoint_url,
        )
    )
