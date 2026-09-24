"""Reads back how Ganesh is wired."""

from src.modules.admin.application.dtos.platform_dto import PlatformSettings
from src.modules.admin.domain.entities.platform import Wiring, read_wiring


class ReadPlatformUseCase:
    """Answers what the administration screen reads.

    It orchestrates and decides nothing: which door is open and what counts as
    a wired service are the domain's business, in `read_wiring`. What this
    adds is the one thing a route may not do — reaching the settings and
    handing them on.
    """

    def __init__(self, settings: PlatformSettings) -> None:
        self._settings = settings

    async def execute(self) -> Wiring:
        settings = self._settings
        return read_wiring(
            environment=settings.environment,
            require_auth=settings.require_auth,
            auth_entra=settings.auth_entra,
            tenant_id=settings.tenant_id,
            has_gemini_key=settings.has_gemini_key,
            gemini_model=settings.gemini_model,
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            s3_bucket=settings.s3_bucket,
            s3_endpoint_url=settings.s3_endpoint_url,
        )
