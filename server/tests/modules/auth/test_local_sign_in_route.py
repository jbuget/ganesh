"""La route de la porte de secours, et ce qu'elle refuse."""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import Settings, get_settings
from src.main import app

URL = "/api/v1/auth/local"

CREDENTIALS = {"login": "admin", "password": "un-mot-de-passe-solide"}


def settings_with(**overrides: object) -> Settings:
    base = {
        "auth_entra": False,
        "auth_login": "admin",
        "auth_password": "un-mot-de-passe-solide",
        "secret_key": "une clef de signature de developpement, bien assez longue",
        "require_auth": True,
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    # Une lambda sans paramètre : FastAPI inspecte la signature de ce qu'on
    # lui donne, et prendrait un **kwargs pour des paramètres de requête.
    app.dependency_overrides[get_settings] = lambda: settings_with()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()


async def test_les_bons_identifiants_rendent_un_jeton(client: AsyncClient) -> None:
    response = await client.post(URL, json=CREDENTIALS)

    assert response.status_code == 200
    assert response.json()["access_token"]


async def test_un_mot_de_passe_faux_est_refuse(client: AsyncClient) -> None:
    response = await client.post(URL, json={**CREDENTIALS, "password": "faux"})

    assert response.status_code == 401
    # Ce qui est refusé ne dit pas lequel des deux champs était faux : cela
    # dirait à qui cherche qu'il tient déjà l'identifiant.
    assert "identifiant" in response.json()["detail"].lower()


async def test_un_identifiant_inconnu_est_refuse(client: AsyncClient) -> None:
    response = await client.post(URL, json={**CREDENTIALS, "login": "quelquun"})

    assert response.status_code == 401


async def test_la_porte_reste_close_quand_entra_est_actif(
    client: AsyncClient,
) -> None:
    """Deux portes ouvertes en même temps, c'est une de trop."""
    app.dependency_overrides[get_settings] = lambda: settings_with(auth_entra=True)

    response = await client.post(URL, json=CREDENTIALS)

    assert response.status_code == 404


async def test_la_porte_reste_close_sans_mot_de_passe_configure(
    client: AsyncClient,
) -> None:
    app.dependency_overrides[get_settings] = lambda: settings_with(auth_password="")

    response = await client.post(URL, json=CREDENTIALS)

    assert response.status_code == 401
