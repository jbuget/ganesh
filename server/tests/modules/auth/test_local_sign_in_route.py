"""The route of the fallback door, and what it turns away."""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import Settings, get_settings
from src.main import app

URL = "/api/v1/auth/local"

CREDENTIALS = {"login": "admin", "password": "a-solid-password"}


def settings_with(**overrides: object) -> Settings:
    base = {
        "auth_entra": False,
        "auth_login": "admin",
        "auth_password": "a-solid-password",
        "secret_key": "a development signing key, long enough by far",
        "require_auth": True,
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    # A lambda taking nothing: FastAPI inspects the signature of what it is
    # given, and would read a **kwargs as query parameters.
    app.dependency_overrides[get_settings] = lambda: settings_with()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()


async def test_right_credentials_return_a_token(client: AsyncClient) -> None:
    response = await client.post(URL, json=CREDENTIALS)

    assert response.status_code == 200
    assert response.json()["access_token"]


async def test_wrong_password_is_refused(client: AsyncClient) -> None:
    response = await client.post(URL, json={**CREDENTIALS, "password": "wrong"})

    assert response.status_code == 401
    # What is refused does not say which of the two fields was wrong: that
    # would tell whoever is trying that they already hold the login.
    assert "identifiant" in response.json()["detail"].lower()


async def test_unknown_login_is_refused(client: AsyncClient) -> None:
    response = await client.post(URL, json={**CREDENTIALS, "login": "someone"})

    assert response.status_code == 401


async def test_accented_password_is_refused_rather_than_raising(
    client: AsyncClient,
) -> None:
    """A 500 where a 401 belongs tells whoever is trying that they found something."""
    app.dependency_overrides[get_settings] = lambda: settings_with(
        auth_password="un-mot-de-passé"
    )

    wrong = await client.post(URL, json={**CREDENTIALS, "password": "wrong"})
    right = await client.post(URL, json={**CREDENTIALS, "password": "un-mot-de-passé"})

    assert wrong.status_code == 401
    assert right.status_code == 200


async def test_the_door_stays_shut_while_entra_is_on(client: AsyncClient) -> None:
    """Two doors open at once is one too many."""
    app.dependency_overrides[get_settings] = lambda: settings_with(auth_entra=True)

    response = await client.post(URL, json=CREDENTIALS)

    assert response.status_code == 404


async def test_the_door_stays_shut_without_a_password_set(
    client: AsyncClient,
) -> None:
    app.dependency_overrides[get_settings] = lambda: settings_with(auth_password="")

    response = await client.post(URL, json=CREDENTIALS)

    assert response.status_code == 401
