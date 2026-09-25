"""The route that gives away who a teammate is, and what it publishes."""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.auth.presentation.dependencies import (
    get_current_manager,
    get_current_user,
)
from src.modules.users.application.use_cases.update_user_identity import (
    UpdateUserIdentityUseCase,
)
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.presentation.dependencies import (
    get_update_user_identity_use_case,
)
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryUserRepository,
)

MANAGER = User(
    id=1,
    entra_oid="oid-1",
    email="j.buget@waat.fr",
    display_name="J. Buget",
    role=Role.MANAGER,
)
TEAMMATE = User(
    id=2,
    entra_oid="oid-2",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)

URL = f"{get_settings().api_prefix}/users/2/identity"


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    users = InMemoryUserRepository([MANAGER, TEAMMATE])
    app.dependency_overrides[get_current_user] = lambda: MANAGER
    app.dependency_overrides[get_current_manager] = lambda: MANAGER
    app.dependency_overrides[get_update_user_identity_use_case] = (
        lambda: UpdateUserIdentityUseCase(
            users=users, audit_logs=InMemoryAuditLogRepository()
        )
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()


async def test_a_manager_writes_the_sheet_of_a_teammate(client: AsyncClient) -> None:
    response = await client.patch(
        URL,
        json={
            "first_name": "Léa",
            "last_name": "Chen",
            "department": "customer_service",
            "github_username": "lea-chen",
            "org_level": "comex",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["first_name"] == "Léa"
    assert body["last_name"] == "Chen"
    assert body["department"] == "customer_service"
    assert body["github_username"] == "lea-chen"
    assert body["org_level"] == "comex"


async def test_a_sheet_may_be_emptied(client: AsyncClient) -> None:
    response = await client.patch(
        URL,
        json={
            "first_name": None,
            "last_name": None,
            "department": None,
            "github_username": None,
        },
    )

    assert response.status_code == 200
    assert response.json()["department"] is None
    assert response.json()["github_username"] is None
    assert response.json()["org_level"] is None


async def test_a_department_outside_the_list_is_refused(client: AsyncClient) -> None:
    """The list is the missions': a free-text department would compare with nothing."""
    response = await client.patch(
        URL,
        json={
            "first_name": "Léa",
            "last_name": "Chen",
            "department": "compta",
            "github_username": None,
        },
    )

    assert response.status_code == 422


async def test_the_name_one_reads_follows_the_civil_name(client: AsyncClient) -> None:
    """Naming a teammate renames them everywhere, initials included."""
    response = await client.patch(
        URL,
        json={
            "first_name": "Léa",
            "last_name": "Chen",
            "department": None,
            "github_username": None,
        },
    )

    body = response.json()
    assert body["display_name"] == "Léa Chen"
    assert body["initials"] == "LC"


async def test_a_handle_written_with_its_at_sign_is_kept_as_the_handle(
    client: AsyncClient,
) -> None:
    """« @lea-chen » is how one writes a handle; the address is built from it."""
    response = await client.patch(
        URL,
        json={
            "first_name": None,
            "last_name": None,
            "department": None,
            "github_username": "@lea-chen",
        },
    )

    assert response.json()["github_username"] == "lea-chen"
