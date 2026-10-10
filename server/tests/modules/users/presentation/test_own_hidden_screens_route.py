"""PUT /users/me/hidden-screens: one's own sidebar, and no other."""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.users.application.use_cases.choose_own_hidden_screens import (
    ChooseOwnHiddenScreensUseCase,
)
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.presentation.dependencies import (
    get_choose_own_hidden_screens_use_case,
)
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryUserRepository,
)

TEAMMATE = User(
    id=2,
    entra_oid="oid-2",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)

URL = f"{get_settings().api_prefix}/users/me/hidden-screens"


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    users = InMemoryUserRepository([TEAMMATE])
    app.dependency_overrides[get_current_user] = lambda: TEAMMATE
    app.dependency_overrides[get_choose_own_hidden_screens_use_case] = (
        lambda: ChooseOwnHiddenScreensUseCase(
            users=users, audit_logs=InMemoryAuditLogRepository()
        )
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()


async def test_a_teammate_hides_two_screens(client: AsyncClient) -> None:
    response = await client.put(URL, json={"screens": ["/stats", "/logs"]})

    assert response.status_code == 200
    assert response.json()["hidden_screens"] == ["/logs", "/stats"]


async def test_the_home_screen_cannot_be_hidden(client: AsyncClient) -> None:
    response = await client.put(URL, json={"screens": ["/"]})

    assert response.status_code == 422


async def test_the_address_names_no_teammate(client: AsyncClient) -> None:
    assert "{" not in URL
    assert URL.endswith("/users/me/hidden-screens")
