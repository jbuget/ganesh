"""Business rules the user carries."""

from datetime import datetime

import pytest

from src.modules.users.domain.entities.user import Role, User


def make_user(role: Role = Role.TEAMMATE, is_active: bool = True) -> User:
    return User(
        id=None,
        entra_oid="oid-1",
        email="d.dehe@waat.fr",
        display_name="D. Dehe",
        role=role,
        is_active=is_active,
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
    """Transparency is deliberate: anyone may fix a colleague's open month."""
    assert make_user(role).can_edit_open_months() is True


def test_a_deactivated_user_can_no_longer_edit_anything() -> None:
    assert make_user(is_active=False).can_edit_open_months() is False


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

    assert user.record_login(datetime(2026, 9, 17, 9, 0)) is True
    assert user.last_login_at == datetime(2026, 9, 17, 9, 0)


def test_a_connection_within_the_freshness_window_is_not_rewritten() -> None:
    """A bearer token is presented on every request.

    Without a freshness window, the « last login » would measure
    nothing but the number of writes to the database.
    """
    user = make_user()
    user.record_login(datetime(2026, 9, 17, 9, 0))

    assert user.record_login(datetime(2026, 9, 17, 9, 3)) is False
    assert user.last_login_at == datetime(2026, 9, 17, 9, 0)


def test_a_connection_after_the_freshness_window_is_recorded() -> None:
    user = make_user()
    user.record_login(datetime(2026, 9, 17, 9, 0))

    assert user.record_login(datetime(2026, 9, 17, 9, 20)) is True
    assert user.last_login_at == datetime(2026, 9, 17, 9, 20)


def test_a_connection_is_never_dated_backwards() -> None:
    """Two concurrent requests may arrive out of order."""
    user = make_user()
    user.record_login(datetime(2026, 9, 17, 9, 0))

    assert user.record_login(datetime(2026, 9, 17, 8, 0)) is False
    assert user.last_login_at == datetime(2026, 9, 17, 9, 0)


def with_id(user: User, user_id: int) -> User:
    user.id = user_id
    return user


def test_a_manager_can_deactivate_someone_else() -> None:
    manager = with_id(make_user(Role.MANAGER), 1)
    other = with_id(make_user(Role.TEAMMATE), 2)

    assert manager.can_deactivate(other) is True


def test_a_manager_cannot_deactivate_themselves() -> None:
    """Cutting off one's own access is locking oneself out."""
    manager = with_id(make_user(Role.MANAGER), 1)

    assert manager.can_deactivate(manager) is False


def test_a_teammate_cannot_deactivate_anyone() -> None:
    teammate = with_id(make_user(Role.TEAMMATE), 1)
    other = with_id(make_user(Role.MANAGER), 2)

    assert teammate.can_deactivate(other) is False


def test_a_deactivated_manager_can_no_longer_deactivate_anyone() -> None:
    manager = with_id(make_user(Role.MANAGER, is_active=False), 1)
    other = with_id(make_user(Role.TEAMMATE), 2)

    assert manager.can_deactivate(other) is False
