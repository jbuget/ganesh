"""Regles metier portees par l'utilisateur."""

import pytest

from src.modules.users.domain.entities.user import Role, User


def make_user(role: Role = Role.TEAMMATE, actif: bool = True) -> User:
    return User(
        id=None,
        entra_oid="oid-1",
        email="d.dehe@waat.fr",
        display_name="D. Dehe",
        role=role,
        actif=actif,
    )


def test_teammate_cannot_reopen_a_validated_month() -> None:
    assert make_user(Role.TEAMMATE).can_reopen_month() is False


def test_manager_can_reopen_a_validated_month() -> None:
    assert make_user(Role.MANAGER).can_reopen_month() is True


def test_teammate_cannot_manage_teammates() -> None:
    assert make_user(Role.TEAMMATE).can_manage_teammates() is False


def test_manager_can_manage_teammates() -> None:
    assert make_user(Role.MANAGER).can_manage_teammates() is True


@pytest.mark.parametrize("role", [Role.TEAMMATE, Role.MANAGER])
def test_any_active_user_can_edit_an_open_month_of_anyone(role: Role) -> None:
    """Transparence assumee : chacun peut corriger un mois ouvert d'un collegue."""
    assert make_user(role).can_edit_open_months() is True


def test_a_deactivated_user_can_no_longer_edit_anything() -> None:
    assert make_user(actif=False).can_edit_open_months() is False


def test_email_is_normalised_to_lowercase() -> None:
    user = User(
        id=None,
        entra_oid="oid-2",
        email="J.Buget@WAAT.fr",
        display_name="J. Buget",
        role=Role.MANAGER,
    )

    assert user.email == "j.buget@waat.fr"
