"""Which one account a name designates.

Used by whoever has to name a person without knowing their identifier. Pure on
purpose: it reads no repository, the caller hands it the accounts it may
choose among.

A name is compared the way a person would read it — case, accents and extra
spaces do not tell two people apart — and an exact name wins over a longer one,
so « Léa Chen » is not made ambiguous by a « Léa Chenevier ». Several matches
are never guessed between: the wrong person told cannot be taken back.
"""

import unicodedata
from collections.abc import Iterable

from src.modules.users.domain.entities.user import User
from src.shared.exceptions.domain_exceptions import DomainError


class NoSuchUserError(DomainError):
    """No account carries that name."""

    def __init__(self, name: str) -> None:
        super().__init__(f"No user is named « {name} ».")
        self.name = name


class AmbiguousUserError(DomainError):
    """Several accounts could be the one that was meant."""

    def __init__(self, name: str, candidates: list[User]) -> None:
        super().__init__(f"« {name} » designates several users.")
        self.name = name
        self.candidates = candidates


def find_one(users: Iterable[User], name: str) -> User:
    """The single account `name` designates among `users`."""
    sought = _plain(name)
    pool = [(user, _names(user)) for user in users] if sought else []
    exact = [user for user, names in pool if sought in names]
    partial = [user for user, names in pool if any(sought in n for n in names)]
    found = exact or partial
    if not found:
        raise NoSuchUserError(name)
    if len(found) > 1:
        raise AmbiguousUserError(name, found)
    return found[0]


def _plain(text: str) -> str:
    bare = unicodedata.normalize("NFKD", text)
    bare = "".join(c for c in bare if not unicodedata.combining(c))
    return " ".join(bare.casefold().split())


def _names(user: User) -> list[str]:
    civil = " ".join(part for part in (user.first_name, user.last_name) if part)
    return [_plain(name) for name in (user.display_name, civil) if name]
