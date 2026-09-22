"""The route that says who is signed in."""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.auth.presentation.dependencies import get_signed_in_user
from src.modules.users.domain.entities.user import Role, User

URL = f"{get_settings().api_prefix}/users/me"

METIER = User(
    id=7,
    entra_oid="oid-7",
    email="a.metier@waat.fr",
    display_name="A. Métier",
    role=Role.REQUESTER,
)


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()


async def test_a_requester_reads_their_own_account(client: AsyncClient) -> None:
    """The one route of the module open to them, and it has to be.

    It is how a screen learns whose account it is drawing: a requester who
    could not read their own name would be shown a blank page instead of
    their needs.
    """
    app.dependency_overrides[get_signed_in_user] = lambda: METIER

    response = await client.get(URL)

    assert response.status_code == 200
    assert response.json()["role"] == "REQUESTER"
    assert response.json()["email"] == "a.metier@waat.fr"
