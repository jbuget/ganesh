"""Business exceptions shared by every module.

The domain raises them; the presentation layer turns them into HTTP
responses. No framework dependency here.
"""


class DomainError(Exception):
    """Generic business error."""


class EntityNotFoundError(DomainError):
    """The requested entity does not exist."""


class ValidationError(DomainError):
    """A business invariant is not satisfied."""


class ForbiddenActionError(DomainError):
    """The actor is not allowed to perform this action."""


class ConflictError(DomainError):
    """The action conflicts with the current state."""


class ServiceUnavailableError(DomainError):
    """Something Ganesh depends on is not answering.

    Not the caller's fault, which is the whole point of telling it apart: a
    400 would send whoever asked looking at their own request.
    """
