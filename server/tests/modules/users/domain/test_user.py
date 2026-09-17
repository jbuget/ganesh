"""Regles metier portees par l'utilisateur."""

from datetime import datetime

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


def test_a_first_connection_is_recorded() -> None:
    user = make_user()

    assert user.enregistrer_connexion(datetime(2026, 9, 17, 9, 0)) is True
    assert user.derniere_connexion == datetime(2026, 9, 17, 9, 0)


def test_a_connection_within_the_freshness_window_is_not_rewritten() -> None:
    """Un jeton porteur est represente a chaque requete.

    Sans fenetre de fraicheur, la « derniere connexion » ne mesurerait plus que
    le nombre d'ecritures en base.
    """
    user = make_user()
    user.enregistrer_connexion(datetime(2026, 9, 17, 9, 0))

    assert user.enregistrer_connexion(datetime(2026, 9, 17, 9, 3)) is False
    assert user.derniere_connexion == datetime(2026, 9, 17, 9, 0)


def test_a_connection_after_the_freshness_window_is_recorded() -> None:
    user = make_user()
    user.enregistrer_connexion(datetime(2026, 9, 17, 9, 0))

    assert user.enregistrer_connexion(datetime(2026, 9, 17, 9, 20)) is True
    assert user.derniere_connexion == datetime(2026, 9, 17, 9, 20)


def test_a_connection_is_never_dated_backwards() -> None:
    """Deux requetes concurrentes peuvent arriver dans le desordre."""
    user = make_user()
    user.enregistrer_connexion(datetime(2026, 9, 17, 9, 0))

    assert user.enregistrer_connexion(datetime(2026, 9, 17, 8, 0)) is False
    assert user.derniere_connexion == datetime(2026, 9, 17, 9, 0)
