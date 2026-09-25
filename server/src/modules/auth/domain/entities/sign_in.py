"""What the fallback door refuses, and why."""

from src.shared.exceptions.domain_exceptions import DomainError, EntityNotFoundError


class FallbackDoorClosedError(EntityNotFoundError):
    """Entra is on, so this door does not exist.

    « Not found » rather than « forbidden », deliberately: a door one can feel
    is a door one can push, and two doors open at once would be one too many.
    It narrows `EntityNotFoundError` so the answer stays a 404 without the
    route having to say so.
    """


class InvalidCredentialsError(DomainError):
    """The login or the password is wrong, and it is never said which.

    Naming the field that failed tells whoever is trying that they already
    hold the other half. The route turns it into a 401 — the one status no
    shared exception maps to, because signing in is the only place it means
    anything.
    """
