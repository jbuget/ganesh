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


@pytest.mark.parametrize("role", [Role.TEAMMATE, Role.MANAGER, Role.ADMIN])
def test_any_active_user_can_edit_an_open_month_of_anyone(role: Role) -> None:
    """Transparency is deliberate: anyone may fix a colleague's open month."""
    assert make_user(role).can_edit_open_months() is True


def test_a_guest_belongs_to_no_month() -> None:
    """Someone of the company but not of the team declares no time."""
    assert make_user(Role.GUEST).can_edit_open_months() is False


def test_a_guest_manages_nobody_and_reopens_nothing() -> None:
    guest = make_user(Role.GUEST)

    assert guest.can_manage_teammates() is False
    assert guest.can_reopen_month() is False


@pytest.mark.parametrize("role", [Role.TEAMMATE, Role.MANAGER, Role.ADMIN])
def test_the_team_is_told_apart_from_whoever_is_only_at_the_door(role: Role) -> None:
    assert make_user(role).is_guest is False
    assert make_user(Role.GUEST).is_guest is True


def test_an_account_opens_nothing_until_somebody_says_who_it_is() -> None:
    """The default role is the one that may do the least."""
    user = User(
        id=None,
        entra_oid="oid-fresh",
        email="fresh@waat.fr",
        display_name="Fresh",
    )

    assert user.role is Role.GUEST


def test_a_deactivated_user_can_no_longer_edit_anything() -> None:
    assert make_user(is_active=False).can_edit_open_months() is False


def test_a_teammate_arbitrates_nothing() -> None:
    assert make_user(Role.TEAMMATE).can_arbitrate_requests() is False


def test_a_manager_arbitrates_what_the_company_asks_for() -> None:
    assert make_user(Role.MANAGER).can_arbitrate_requests() is True


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


# --- The ladder ------------------------------------------------------------


def test_the_ladder_goes_from_the_guest_to_the_admin() -> None:
    """The declaration order is the ladder, and nothing else reads it."""
    assert [role.rank for role in Role] == [0, 1, 2, 3]
    assert Role.ADMIN.reaches(Role.MANAGER) is True
    assert Role.MANAGER.reaches(Role.ADMIN) is False
    assert Role.MANAGER.reaches(Role.MANAGER) is True


def test_an_admin_steers_the_team_like_a_manager() -> None:
    """The top rung is never weaker than the one below it."""
    admin = make_user(Role.ADMIN)

    assert admin.is_manager is True
    assert admin.can_reopen_month() is True
    assert admin.can_manage_teammates() is True
    assert admin.can_arbitrate_requests() is True


def test_a_manager_is_not_an_admin() -> None:
    assert make_user(Role.MANAGER).is_admin is False
    assert make_user(Role.ADMIN).is_admin is True


# --- Declaring an account --------------------------------------------------


@pytest.mark.parametrize("role", [Role.MANAGER, Role.ADMIN])
def test_a_manager_and_an_admin_both_declare_an_account(role: Role) -> None:
    assert make_user(role).can_declare_user() is True


@pytest.mark.parametrize("role", [Role.GUEST, Role.TEAMMATE])
def test_nobody_below_a_manager_declares_an_account(role: Role) -> None:
    assert make_user(role).can_declare_user() is False


def test_a_deactivated_manager_declares_nobody() -> None:
    assert make_user(Role.MANAGER, is_active=False).can_declare_user() is False


# --- Conferring a rank -----------------------------------------------------


def test_a_manager_confers_up_to_their_own_rank() -> None:
    manager = make_user(Role.MANAGER)

    assert manager.can_grant(Role.TEAMMATE) is True
    assert manager.can_grant(Role.MANAGER) is True
    assert manager.can_grant(Role.ADMIN) is False


def test_an_admin_confers_every_rank() -> None:
    admin = make_user(Role.ADMIN)

    assert all(admin.can_grant(role) for role in Role)


def test_a_teammate_confers_nothing() -> None:
    teammate = make_user(Role.TEAMMATE)

    assert all(teammate.can_grant(role) is False for role in Role)


def test_a_manager_promotes_a_teammate() -> None:
    manager = with_id(make_user(Role.MANAGER), 1)
    teammate = with_id(make_user(Role.TEAMMATE), 2)

    assert manager.can_change_role_of(teammate, Role.MANAGER) is True


def test_a_manager_cannot_touch_an_admin() -> None:
    """Otherwise the rung above would hold nothing."""
    manager = with_id(make_user(Role.MANAGER), 1)
    admin = with_id(make_user(Role.ADMIN), 2)

    assert manager.can_change_role_of(admin, Role.TEAMMATE) is False


def test_an_admin_demotes_another_admin() -> None:
    admin = with_id(make_user(Role.ADMIN), 1)
    peer = with_id(make_user(Role.ADMIN), 2)

    assert admin.can_change_role_of(peer, Role.TEAMMATE) is True


def test_nobody_changes_their_own_rank() -> None:
    """Demoting oneself is a one-way trip: no route promotes one back."""
    admin = with_id(make_user(Role.ADMIN), 1)

    assert admin.can_change_role_of(admin, Role.TEAMMATE) is False
    assert admin.can_change_role_of(admin, Role.ADMIN) is False


def test_the_last_admin_is_protected_by_those_two_rules_alone() -> None:
    """Nobody below reaches them, and they do not reach themselves."""
    admin = with_id(make_user(Role.ADMIN), 1)
    manager = with_id(make_user(Role.MANAGER), 2)

    assert manager.can_change_role_of(admin, Role.MANAGER) is False
    assert manager.can_deactivate(admin) is False
    assert admin.can_change_role_of(admin, Role.MANAGER) is False
    assert admin.can_deactivate(admin) is False
