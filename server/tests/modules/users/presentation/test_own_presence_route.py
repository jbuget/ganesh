"""The route by which everyone says their own week, and nobody else's."""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.users.application.use_cases.declare_own_presence import (
    DeclareOwnPresenceUseCase,
)
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.presentation.dependencies import (
    get_declare_own_presence_use_case,
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

URL = f"{get_settings().api_prefix}/users/me/presence"

A_WEEK = {
    "monday": "ON_SITE",
    "tuesday": "ON_SITE",
    "wednesday": "REMOTE",
    "thursday": "ON_SITE",
    "friday": "AWAY",
}


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    users = InMemoryUserRepository([TEAMMATE])
    app.dependency_overrides[get_current_user] = lambda: TEAMMATE
    app.dependency_overrides[get_declare_own_presence_use_case] = (
        lambda: DeclareOwnPresenceUseCase(
            users=users, audit_logs=InMemoryAuditLogRepository()
        )
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()


async def test_a_teammate_says_their_week(client: AsyncClient) -> None:
    response = await client.put(URL, json=A_WEEK)

    assert response.status_code == 200
    assert response.json()["presence"]["wednesday"] == "REMOTE"


async def test_the_office_is_counted_by_the_api(client: AsyncClient) -> None:
    # Two views counting it themselves would eventually count it differently.
    response = await client.put(URL, json=A_WEEK)

    presence = response.json()["presence"]
    assert presence["days_on_site"] == 3
    assert presence["days_present"] == 4


async def test_somewhere_that_is_not_one_of_the_three_is_refused(
    client: AsyncClient,
) -> None:
    response = await client.put(URL, json={**A_WEEK, "monday": "au bureau"})

    assert response.status_code == 422


async def test_a_week_left_unsaid_is_a_week_at_the_office(client: AsyncClient) -> None:
    # The common case, so declaring a Wednesday at home takes one field.
    response = await client.put(URL, json={"wednesday": "REMOTE"})

    assert response.status_code == 200
    assert response.json()["presence"]["days_on_site"] == 4


async def test_there_is_no_route_to_speak_for_somebody_else(
    client: AsyncClient,
) -> None:
    response = await client.put(
        f"{get_settings().api_prefix}/users/2/presence", json=A_WEEK
    )

    assert response.status_code == 404
