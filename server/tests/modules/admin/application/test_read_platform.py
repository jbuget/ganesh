"""Reading back how the platform is wired."""

from src.modules.admin.application.dtos.platform_dto import PlatformSettings
from src.modules.admin.application.use_cases.read_platform import ReadPlatformUseCase
from src.modules.admin.domain.entities.platform import Door

WIRED = PlatformSettings(
    environment="production",
    require_auth=True,
    auth_entra=True,
    tenant_id="tenant-1",
    has_gemini_key=True,
    gemini_model="gemini-3.8-flash",
    smtp_host="smtp.mailgun.org",
    smtp_port=587,
    s3_bucket="ganesh-attachments",
    s3_endpoint_url="",
)


def a_platform(**changes: object) -> ReadPlatformUseCase:
    return ReadPlatformUseCase(PlatformSettings(**{**vars(WIRED), **changes}))


async def test_the_reading_names_the_door_and_every_service() -> None:
    wiring = await a_platform().execute()

    assert wiring.door is Door.ENTRA
    assert wiring.environment == "production"
    assert {service.name for service in wiring.services} == {
        "entra",
        "gemini",
        "smtp",
        "s3",
    }


async def test_authentication_switched_off_leaves_no_door() -> None:
    wiring = await a_platform(require_auth=False).execute()

    assert wiring.door is Door.OPEN


async def test_a_service_nobody_wired_comes_back_as_such() -> None:
    wiring = await a_platform(has_gemini_key=False).execute()

    gemini = next(one for one in wiring.services if one.name == "gemini")
    assert gemini.configured is False
