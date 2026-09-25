"""Who the door lets through, once an identity has been recognised."""

import pytest
from fastapi import HTTPException

from src.modules.auth.presentation.dependencies import admit, dev_identity
from src.modules.users.domain.entities.user import Role, User


def make_user(role: Role = Role.TEAMMATE, is_active: bool = True) -> User:
    return User(
        id=1,
        entra_oid="oid-1",
        email="d.dehe@waat.fr",
        display_name="D. Dehe",
        role=role,
        is_active=is_active,
    )


@pytest.mark.parametrize("role", [Role.TEAMMATE, Role.MANAGER])
def test_the_team_comes_in(role: Role) -> None:
    user = make_user(role)

    assert admit(user) is user


def test_a_deactivated_account_is_turned_away() -> None:
    with pytest.raises(HTTPException) as refusal:
        admit(make_user(is_active=False))

    assert refusal.value.status_code == 403


def test_a_guest_is_turned_away() -> None:
    """The door opens on the application; the requests open their own."""
    with pytest.raises(HTTPException) as refusal:
        admit(make_user(Role.GUEST))

    assert refusal.value.status_code == 403


def test_the_open_door_hands_over_the_account_it_is_told_to() -> None:
    """Development only, and the whole point of it.

    Two audiences read this application: passing from one to the other must
    take one line of configuration, and `make grant-role` moves the account
    the open door hands over from one audience to the other.
    """
    assert dev_identity("a.metier@waat.fr").email == "a.metier@waat.fr"


def test_two_development_accounts_are_never_taken_for_one_another() -> None:
    """A fixed id would match whoever was provisioned first."""
    assert dev_identity("a.metier@waat.fr").oid != dev_identity("j.buget@waat.fr").oid
