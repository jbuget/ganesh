"""Business rules the user carries."""

from datetime import datetime

import pytest

from src.modules.users.domain.entities.user import Role, User
from src.shared.enums.department import Department
from src.shared.enums.org_level import OrgLevel


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


def test_a_requester_belongs_to_no_month() -> None:
    """Someone who only expresses needs declares no time, their own included."""
    assert make_user(Role.REQUESTER).can_edit_open_months() is False


def test_a_requester_manages_nobody_and_reopens_nothing() -> None:
    requester = make_user(Role.REQUESTER)

    assert requester.can_manage_teammates() is False
    assert requester.can_reopen_month() is False


@pytest.mark.parametrize("role", [Role.TEAMMATE, Role.MANAGER])
def test_the_team_is_told_apart_from_whoever_only_asks(role: Role) -> None:
    assert make_user(role).is_requester is False
    assert make_user(Role.REQUESTER).is_requester is True


def test_an_account_opens_nothing_until_somebody_says_who_it_is() -> None:
    """The default role is the one that may do the least."""
    user = User(
        id=None,
        entra_oid="oid-fresh",
        email="fresh@waat.fr",
        display_name="Fresh",
    )

    assert user.role is Role.REQUESTER


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


def test_a_civil_name_is_trimmed() -> None:
    user = make_user()
    user.set_identity(
        first_name="  Léa  ",
        last_name=" Chen ",
        department=None,
        github_username=None,
        org_level=None,
    )

    assert user.first_name == "Léa"
    assert user.last_name == "Chen"


def test_a_blank_name_reads_as_unknown_rather_than_empty() -> None:
    """« » and « nothing » say the same thing; the database should say it once."""
    user = make_user()
    user.set_identity(
        first_name="   ",
        last_name="",
        department=None,
        github_username=None,
        org_level=None,
    )

    assert user.first_name is None
    assert user.last_name is None


def test_a_teammate_belongs_to_one_department() -> None:
    user = make_user()
    user.set_identity(
        first_name="Léa",
        last_name="Chen",
        department=Department.CUSTOMER_SERVICE,
        github_username=None,
        org_level=None,
    )

    assert user.department is Department.CUSTOMER_SERVICE


def test_the_name_one_reads_is_the_civil_one_once_it_is_known() -> None:
    user = make_user()
    user.set_identity(
        first_name="Léa",
        last_name="Chen",
        department=None,
        github_username=None,
        org_level=None,
    )

    assert user.label == "Léa Chen"


def test_a_half_known_name_is_still_better_than_the_account_one() -> None:
    user = make_user()
    user.set_identity(
        first_name="Léa",
        last_name=None,
        department=None,
        github_username=None,
        org_level=None,
    )

    assert user.label == "Léa"


def test_the_account_name_stands_in_as_long_as_nobody_has_said_who_it_is() -> None:
    """Entra names the account; it does not say who one is talking to."""
    assert make_user().label == "D. Dehe"


def test_a_github_handle_is_kept_as_the_handle_alone() -> None:
    """« @lea-chen » is how one writes a handle; « lea-chen » is what it is."""
    user = make_user()
    user.set_identity(
        first_name=None,
        last_name=None,
        department=None,
        github_username=" @lea-chen ",
        org_level=None,
    )

    assert user.github_username == "lea-chen"


def test_a_blank_github_handle_reads_as_unknown() -> None:
    user = make_user()
    user.set_identity(
        first_name=None,
        last_name=None,
        department=None,
        github_username="  ",
        org_level=None,
    )

    assert user.github_username is None


def test_a_teammate_sits_somewhere_in_the_organisation() -> None:
    user = make_user()
    user.set_identity(
        first_name="Léa",
        last_name="Chen",
        department=Department.CUSTOMER_SERVICE,
        github_username=None,
        org_level=OrgLevel.COMEX,
    )

    assert user.org_level is OrgLevel.COMEX


def test_a_level_nobody_has_said_reads_as_unknown() -> None:
    """Three hundred people sign in; nobody qualifies them one by one."""
    assert make_user().org_level is None
