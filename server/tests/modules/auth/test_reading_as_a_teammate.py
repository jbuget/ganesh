"""An administrator reads Ganesh through a teammate's eyes, and writes nothing.

Two halves, tested apart: who may borrow an account at all, and what a
borrowed account may then do. The second is the guarantee the feature rests
on — `test_write_doors` says every gesture hangs off a door, and every one of
those doors asks `can_act()`.
"""

from collections.abc import Iterator

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.api_keys.presentation.dependencies import teammate_or_machine
from src.modules.auth.presentation.dependencies import (
    borrowed_id,
    get_asker,
    get_current_user,
    get_signed_in_user,
    read_as,
)
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.domain.repositories.user_repository import UserRepository

API = get_settings().api_prefix


def make_user(
    user_id: int = 1, role: Role = Role.TEAMMATE, is_active: bool = True
) -> User:
    return User(
        id=user_id,
        entra_oid=f"oid-{user_id}",
        email=f"user{user_id}@waat.fr",
        display_name=f"User {user_id}",
        role=role,
        is_active=is_active,
    )


class InMemoryUsers(UserRepository):
    """The team, held in a dict: the borrowing reads one row and no more."""

    def __init__(self, *users: User) -> None:
        self.users = {user.id: user for user in users}

    async def get_by_id(self, user_id: int) -> User | None:
        return self.users.get(user_id)

    async def get_by_entra_oid(self, entra_oid: str) -> User | None:  # pragma: no cover
        raise NotImplementedError

    async def get_by_email(self, email: str) -> User | None:  # pragma: no cover
        raise NotImplementedError

    async def list_all(self, include_inactive: bool = False) -> list[User]:
        return list(self.users.values())

    async def add(self, user: User) -> User:  # pragma: no cover
        raise NotImplementedError

    async def update(self, user: User) -> User:  # pragma: no cover
        raise NotImplementedError


# --- Who may borrow an account ------------------------------------------


async def test_an_administrator_reads_as_a_teammate() -> None:
    admin = make_user(1, Role.ADMIN)
    teammate = make_user(2)

    read = await read_as(admin, 2, InMemoryUsers(admin, teammate))  # type: ignore[arg-type]

    assert read.id == 2
    assert read.impersonated_by is admin


@pytest.mark.parametrize("role", [Role.GUEST, Role.TEAMMATE, Role.MANAGER])
async def test_nobody_below_an_administrator_borrows_an_account(role: Role) -> None:
    """A manager reads the team's screens, not from inside somebody's account."""
    borrower = make_user(1, role)
    teammate = make_user(2)

    with pytest.raises(HTTPException) as refusal:
        await read_as(borrower, 2, InMemoryUsers(borrower, teammate))  # type: ignore[arg-type]

    assert refusal.value.status_code == 403


async def test_a_borrowed_session_does_not_borrow_again() -> None:
    """Two bands would say two different names over the same screen."""
    admin = make_user(1, Role.ADMIN)
    admin.impersonated_by = make_user(9, Role.ADMIN)

    with pytest.raises(HTTPException) as refusal:
        await read_as(admin, 2, InMemoryUsers(admin, make_user(2)))  # type: ignore[arg-type]

    assert refusal.value.status_code == 403


async def test_an_unknown_teammate_is_not_an_account_to_read() -> None:
    admin = make_user(1, Role.ADMIN)

    with pytest.raises(HTTPException) as refusal:
        await read_as(admin, 404, InMemoryUsers(admin))  # type: ignore[arg-type]

    assert refusal.value.status_code == 404


async def test_a_deactivated_account_has_nothing_to_show() -> None:
    """Behind a closed door there is no screen to go and look at."""
    admin = make_user(1, Role.ADMIN)
    gone = make_user(2, is_active=False)

    with pytest.raises(HTTPException) as refusal:
        await read_as(admin, 2, InMemoryUsers(admin, gone))  # type: ignore[arg-type]

    assert refusal.value.status_code == 403


async def test_one_does_not_borrow_ones_own_account() -> None:
    admin = make_user(1, Role.ADMIN)

    with pytest.raises(HTTPException) as refusal:
        await read_as(admin, 1, InMemoryUsers(admin))  # type: ignore[arg-type]

    assert refusal.value.status_code == 400


@pytest.mark.parametrize("header", [None, "", "  ", "lea", "3.5"])
def test_a_header_that_names_nobody_borrows_nothing(header: str | None) -> None:
    """Ignored rather than refused: a 422 would close every screen at once."""
    assert borrowed_id(header) is None


def test_a_header_naming_a_teammate_is_read_as_one() -> None:
    assert borrowed_id("12") == 12


# --- What a borrowed account may do -------------------------------------


@pytest.fixture(autouse=True)
def _forget_the_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


def borrowed(role: Role = Role.MANAGER) -> User:
    """A manager read by an administrator: the most empowered borrowing there is."""
    target = make_user(2, role)
    target.impersonated_by = make_user(1, Role.ADMIN)
    return target


def reading_as(role: Role = Role.MANAGER) -> AsyncClient:
    user = borrowed(role)
    for seam in (get_signed_in_user, get_current_user, get_asker, teammate_or_machine):
        app.dependency_overrides[seam] = lambda user=user: user
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.parametrize(
    "method,path",
    [
        ("PUT", f"{API}/entries"),
        ("POST", f"{API}/projects"),
        ("PUT", f"{API}/moods"),
        ("PUT", f"{API}/users/me/presence"),
        ("PUT", f"{API}/users/me/reminder-cadence"),
        ("PATCH", f"{API}/users/2/role"),
        ("POST", f"{API}/gazette"),
        # The recueil is the one thing a guest writes, and therefore the one
        # place a borrowed session could have slipped through.
        ("POST", f"{API}/requests"),
        ("PATCH", f"{API}/requests/1"),
        ("POST", f"{API}/requests/1/submit"),
        ("DELETE", f"{API}/requests/1"),
    ],
)
async def test_a_borrowed_session_writes_nothing(method: str, path: str) -> None:
    """403 and not 422: the refusal is about who asks, not about what they sent."""
    response = await reading_as().request(method, path, json={})

    assert response.status_code == 403


async def test_a_borrowed_session_still_reads() -> None:
    """Guards the reading above: a session refused everywhere would pass it."""
    response = await reading_as().get(f"{API}/requests/mine")

    assert response.status_code != 403
