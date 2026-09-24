"""Business rules the user carries."""

from datetime import datetime

import pytest

from src.modules.users.domain.entities.reminder_cadence import ReminderCadence
from src.modules.users.domain.entities.user import Role, User
from src.shared.enums.department import Department


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


def test_a_civil_name_is_trimmed() -> None:
    user = make_user()
    user.set_identity(
        first_name="  Léa  ",
        last_name=" Chen ",
        department=None,
        github_username=None,
    )

    assert user.first_name == "Léa"
    assert user.last_name == "Chen"


def test_a_blank_name_reads_as_unknown_rather_than_empty() -> None:
    """« » and « nothing » say the same thing; the database should say it once."""
    user = make_user()
    user.set_identity(
        first_name="   ", last_name="", department=None, github_username=None
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
    )

    assert user.department is Department.CUSTOMER_SERVICE


def test_the_name_one_reads_is_the_civil_one_once_it_is_known() -> None:
    user = make_user()
    user.set_identity(
        first_name="Léa", last_name="Chen", department=None, github_username=None
    )

    assert user.label == "Léa Chen"


def test_a_half_known_name_is_still_better_than_the_account_one() -> None:
    user = make_user()
    user.set_identity(
        first_name="Léa", last_name=None, department=None, github_username=None
    )

    assert user.label == "Léa"


def test_the_account_name_stands_in_as_long_as_nobody_has_said_who_it_is() -> None:
    """Entra names the account; it does not say who one is talking to."""
    assert make_user().label == "D. Dehe"


def test_a_github_handle_is_kept_as_the_handle_alone() -> None:
    """« @lea-chen » is how one writes a handle; « lea-chen » is what it is."""
    user = make_user()
    user.set_identity(
        first_name=None, last_name=None, department=None, github_username=" @lea-chen "
    )

    assert user.github_username == "lea-chen"


def test_a_blank_github_handle_reads_as_unknown() -> None:
    user = make_user()
    user.set_identity(
        first_name=None, last_name=None, department=None, github_username="  "
    )

    assert user.github_username is None


def test_a_letter_comes_every_day_until_somebody_says_otherwise() -> None:
    # Not a stand-in for an answer nobody gave: a reader who has said nothing
    # is a reader the bell is not reaching, which is the whole point.
    assert make_user().reminder_cadence is ReminderCadence.DAILY


def test_everyone_chooses_how_often_they_are_written_to() -> None:
    assert make_user().can_choose_own_reminder() is True


def test_a_deactivated_account_chooses_nothing() -> None:
    assert make_user(is_active=False).can_choose_own_reminder() is False


def test_a_reader_asks_for_the_weekly_letter() -> None:
    user = make_user()

    user.choose_reminder_cadence(ReminderCadence.WEEKLY)

    assert user.reminder_cadence is ReminderCadence.WEEKLY


def test_a_reader_asks_for_no_letter_at_all() -> None:
    user = make_user()

    user.choose_reminder_cadence(ReminderCadence.NEVER)

    assert user.reminder_cadence is ReminderCadence.NEVER
    assert user.reminder_cadence.wants_mail is False


@pytest.mark.parametrize("cadence", [ReminderCadence.DAILY, ReminderCadence.WEEKLY])
def test_every_cadence_but_never_is_owed_a_letter(cadence: ReminderCadence) -> None:
    assert cadence.wants_mail is True


# --- The ladder of roles -----------------------------------------------------


def test_the_roles_are_ordered_from_the_door_to_the_platform() -> None:
    """The ladder is read by the whole application; its order is a fact."""
    assert list(Role) == [Role.GUEST, Role.TEAMMATE, Role.MANAGER, Role.ADMIN]


@pytest.mark.parametrize("role", [Role.TEAMMATE, Role.MANAGER, Role.ADMIN])
def test_anyone_but_a_guest_may_write(role: Role) -> None:
    assert make_user(role).can_write() is True


def test_a_guest_writes_nothing() -> None:
    """The default role of a first sign-in: it reads, and declares nothing."""
    assert make_user(Role.GUEST).can_write() is False


def test_a_guest_cannot_edit_an_open_month() -> None:
    assert make_user(Role.GUEST).can_edit_open_months() is False


def test_a_guest_declares_neither_their_week_nor_their_cadence() -> None:
    guest = make_user(Role.GUEST)

    assert guest.can_declare_own_presence() is False
    assert guest.can_choose_own_reminder() is False


def test_a_guest_manages_nobody_and_reopens_nothing() -> None:
    guest = make_user(Role.GUEST)

    assert guest.can_manage_teammates() is False
    assert guest.can_reopen_month() is False


# --- An admin is a manager, and more -----------------------------------------


def test_an_admin_carries_every_right_a_manager_carries() -> None:
    admin = make_user(Role.ADMIN)

    assert admin.can_manage_teammates() is True
    assert admin.can_reopen_month() is True
    assert admin.is_manager is True


def test_only_an_admin_administrates_the_platform() -> None:
    assert make_user(Role.ADMIN).can_administrate() is True
    assert make_user(Role.MANAGER).can_administrate() is False
    assert make_user(Role.TEAMMATE).can_administrate() is False
    assert make_user(Role.GUEST).can_administrate() is False


def test_a_deactivated_admin_administrates_nothing() -> None:
    """Being turned away at the door outranks every role."""
    assert make_user(Role.ADMIN, is_active=False).can_administrate() is False


# --- Who may hand out which role ---------------------------------------------


def _pair(actor_role: Role, target_role: Role) -> tuple[User, User]:
    actor = make_user(actor_role)
    actor.id = 1
    target = make_user(target_role)
    target.id = 2
    return actor, target


@pytest.mark.parametrize("granted", [Role.GUEST, Role.TEAMMATE, Role.MANAGER])
def test_a_manager_promotes_up_to_manager(granted: Role) -> None:
    actor, target = _pair(Role.MANAGER, Role.GUEST)

    assert actor.can_change_role_of(target, granted) is True


def test_a_manager_cannot_make_anybody_an_admin() -> None:
    """Nobody hands out more than they hold."""
    actor, target = _pair(Role.MANAGER, Role.TEAMMATE)

    assert actor.can_change_role_of(target, Role.ADMIN) is False


def test_a_manager_cannot_touch_an_admin() -> None:
    """Demoting the one who could undo it is the same door, read backwards."""
    actor, target = _pair(Role.MANAGER, Role.ADMIN)

    assert actor.can_change_role_of(target, Role.TEAMMATE) is False


@pytest.mark.parametrize("granted", list(Role))
def test_an_admin_hands_out_every_role(granted: Role) -> None:
    actor, target = _pair(Role.ADMIN, Role.GUEST)

    assert actor.can_change_role_of(target, granted) is True


def test_an_admin_may_demote_another_admin() -> None:
    actor, target = _pair(Role.ADMIN, Role.ADMIN)

    assert actor.can_change_role_of(target, Role.MANAGER) is True


@pytest.mark.parametrize("role", [Role.GUEST, Role.TEAMMATE])
def test_neither_a_guest_nor_a_teammate_changes_a_role(role: Role) -> None:
    actor, target = _pair(role, Role.GUEST)

    assert actor.can_change_role_of(target, Role.TEAMMATE) is False


def test_nobody_changes_their_own_role() -> None:
    """The same reason nobody deactivates themselves.

    An admin demoting themselves would leave the platform with one fewer
    administrator and no way back in from the inside.
    """
    actor = make_user(Role.ADMIN)
    actor.id = 1

    assert actor.can_change_role_of(actor, Role.TEAMMATE) is False


def test_a_manager_sends_the_round_by_hand() -> None:
    assert make_user(Role.MANAGER).can_run_reminders() is True


def test_a_teammate_does_not_send_the_round_by_hand() -> None:
    # It writes to the whole team at once.
    assert make_user(Role.TEAMMATE).can_run_reminders() is False


def test_a_deactivated_manager_sends_nothing() -> None:
    assert make_user(Role.MANAGER, is_active=False).can_run_reminders() is False
