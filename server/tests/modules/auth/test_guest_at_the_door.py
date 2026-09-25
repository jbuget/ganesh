"""A guest reads Ganesh whole, and writes nothing into it.

`test_write_doors` reads the doors off the application; this one walks
through a few of them, so that the refusal is a thing the API actually says
and not only a dependency graph that looks right.
"""

from collections.abc import Iterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.api_keys.presentation.dependencies import teammate_or_machine
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.users.domain.entities.user import Role, User

API = get_settings().api_prefix


def who(role: Role) -> User:
    return User(
        id=1,
        entra_oid="oid-1",
        email="n.garo@waat.fr",
        display_name="N. Garo",
        role=role,
    )


def sign_in(role: Role) -> AsyncClient:
    # Both seams: a route the team alone reaches declares `get_current_user`,
    # and a route a machine also reaches declares `teammate_or_machine`, which
    # *calls* the first rather than declaring it.
    app.dependency_overrides[get_current_user] = lambda: who(role)
    app.dependency_overrides[teammate_or_machine] = lambda: who(role)
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture(autouse=True)
def _forget_the_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("PUT", f"{API}/entries", {}),
        ("POST", f"{API}/projects", {}),
        ("PUT", f"{API}/moods", {}),
        ("POST", f"{API}/projects/1/updates", {}),
        ("PUT", f"{API}/users/me/presence", {}),
        ("POST", f"{API}/gazette", {}),
        ("POST", f"{API}/planning/simulations", {}),
    ],
)
async def test_a_guest_is_turned_back_before_the_payload_is_even_read(
    method: str, path: str, body: dict[str, object]
) -> None:
    """403 and not 422: the refusal is about who asks, not about what they sent."""
    response = await sign_in(Role.GUEST).request(method, path, json=body)

    assert response.status_code == 403


async def test_the_same_call_from_a_teammate_gets_past_the_door() -> None:
    """Guards the reading above: a route refusing everyone would pass it."""
    response = await sign_in(Role.TEAMMATE).request("PUT", f"{API}/moods", json={})

    assert response.status_code != 403
