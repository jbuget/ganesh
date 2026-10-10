"""Counting the accounts of the platform, rung by rung."""

from src.modules.stats.domain.entities.statistics import Accounts
from src.modules.users.domain.entities.reminder_cadence import ReminderCadence
from src.modules.users.domain.entities.user import Role, User


def census_of(accounts: list[User]) -> Accounts:
    """Reads the accounts as they stand, whoever signed in and whoever did not.

    The letter is read over the accounts that can declare only: a guest is
    given no setting to turn it down with, so their `NEVER` is a default
    nobody chose and would drag the share of those who asked down for nothing.
    """
    writers = [account for account in accounts if account.can_write()]

    def with_role(role: Role) -> int:
        return sum(1 for account in accounts if account.role is role)

    def with_cadence(cadence: ReminderCadence) -> int:
        return sum(1 for account in writers if account.reminder_cadence is cadence)

    return Accounts(
        guests=with_role(Role.GUEST),
        teammates=with_role(Role.TEAMMATE),
        managers=with_role(Role.MANAGER),
        admins=with_role(Role.ADMIN),
        never_signed_in=sum(1 for account in writers if account.last_login_at is None),
        reminders_daily=with_cadence(ReminderCadence.DAILY),
        reminders_weekly=with_cadence(ReminderCadence.WEEKLY),
        reminders_never=with_cadence(ReminderCadence.NEVER),
    )
