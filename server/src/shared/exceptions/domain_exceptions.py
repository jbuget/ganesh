"""Business exceptions shared by every module.

The domain raises them; the presentation layer turns them into HTTP
responses. No framework dependency here.
"""


class DomainError(Exception):
    """Erreur metier generique."""


class EntityNotFoundError(DomainError):
    """The requested entity does not exist."""


class ValidationError(DomainError):
    """A business invariant is not satisfied."""


class ForbiddenActionError(DomainError):
    """The actor is not allowed to perform this action."""


class ConflictError(DomainError):
    """The action conflicts with the current state."""
