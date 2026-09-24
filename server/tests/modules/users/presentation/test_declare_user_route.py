"""The route that makes an account exist before its first sign-in."""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.auth.presentation.dependencies import (
    get_current_manager,
    get_current_user,
)
from src.modules.users.application.use_cases.declare_user import DeclareUserUseCase
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.presentation.dependencies import get_declare_user_use_case
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

URL = f"{get_settings().api_prefix}/users"


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    users = InMemoryUserRepository([MANAGER])
    app.dependency_overrides[get_current_user] = lambda: MANAGER
    app.dependency_overrides[get_current_manager] = lambda: MANAGER
    app.dependency_overrides[get_declare_user_use_case] = lambda: DeclareUserUseCase(
        users=users, audit_logs=InMemoryAuditLogRepository()
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()


def body(**overrides) -> dict:
    payload = {
        "email": "n.arrivee@waat.fr",
        "first_name": "Nina",
        "last_name": "Arrivée",
        "role": "TEAMMATE",
    }
    payload.update(overrides)
    return payload


async def test_a_manager_declares_a_teammate(client: AsyncClient) -> None:
    response = await client.post(URL, json=body(department="customer_service"))

    assert response.status_code == 201
    declared = response.json()
    assert declared["email"] == "n.arrivee@waat.fr"
    assert declared["display_name"] == "Nina Arrivée"
    assert declared["role"] == "TEAMMATE"
    assert declared["department"] == "customer_service"
    assert declared["last_login_at"] is None


async def test_a_manager_cannot_declare_an_admin(client: AsyncClient) -> None:
    response = await client.post(URL, json=body(role="ADMIN"))

    assert response.status_code == 403


async def test_an_address_the_register_already_knows_is_refused(
    client: AsyncClient,
) -> None:
    response = await client.post(URL, json=body(email="J.Buget@waat.fr"))

    assert response.status_code == 409


async def test_a_declaration_without_a_name_is_refused(client: AsyncClient) -> None:
    response = await client.post(URL, json=body(first_name=""))

    assert response.status_code == 422
