"""Who the dashboard expects a month from."""

from src.modules.users.domain.entities.user import User


def who_declares(accounts: list[User]) -> list[User]:
    """The accounts that can fill in a month, out of everyone who signed in.

    The whole company comes through the same Entra tenant, so most accounts
    start as guests: they reach the recueil and nothing else, and hold no
    month. Counting them among those expected would name them as having
    declared nothing for a door that was never open to them, and would make
    every month look unvalidated for want of a hand to validate it.
    """
    return [account for account in accounts if account.can_write()]
