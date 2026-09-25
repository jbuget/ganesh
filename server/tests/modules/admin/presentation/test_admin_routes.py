"""The one route of the administration, and the one door it opens on."""

from collections.abc import Iterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.users.domain.entities.user import Role, User

PLATFORM = f"{get_settings().api_prefix}/admin/platform"


def who(role: Role) -> User:
    return User(
        id=1,
        entra_oid="oid-1",
        email="l.chen@waat.fr",
        display_name="L. Chen",
        role=role,
    )


def sign_in(role: Role) -> AsyncClient:
    app.dependency_overrides[get_current_user] = lambda: who(role)
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture(autouse=True)
def _forget_the_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


async def test_an_admin_reads_how_the_platform_is_wired() -> None:
    response = await sign_in(Role.ADMIN).get(PLATFORM)

    assert response.status_code == 200
    body = response.json()
    assert {service["name"] for service in body["services"]} == {
        "entra",
        "gemini",
        "smtp",
        "s3",
    }


@pytest.mark.parametrize("role", [Role.GUEST, Role.TEAMMATE, Role.MANAGER])
async def test_nobody_below_an_admin_opens_the_administration(role: Role) -> None:
    """A manager manages the team; the platform is another door."""
    response = await sign_in(role).get(PLATFORM)

    assert response.status_code == 403
