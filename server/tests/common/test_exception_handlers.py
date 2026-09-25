"""What status a business error comes back as."""

from fastapi import status

from src.common.exception_handlers import status_for
from src.shared.exceptions.domain_exceptions import (
    ConflictError,
    DomainError,
    EntityNotFoundError,
    ForbiddenActionError,
    ServiceUnavailableError,
    ValidationError,
)


class NarrowerError(ServiceUnavailableError):
    """A module saying the same thing more precisely."""


def test_each_error_has_its_own_status() -> None:
    assert status_for(EntityNotFoundError()) == status.HTTP_404_NOT_FOUND
    assert status_for(ValidationError()) == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert status_for(ForbiddenActionError()) == status.HTTP_403_FORBIDDEN
    assert status_for(ConflictError()) == status.HTTP_409_CONFLICT
    assert status_for(ServiceUnavailableError()) == status.HTTP_503_SERVICE_UNAVAILABLE


def test_a_narrowed_error_keeps_the_status_of_what_it_narrows() -> None:
    # Without this, a module's own exception falls through to 400 and sends
    # the caller looking at their own request for somebody else's outage.
    assert status_for(NarrowerError()) == status.HTTP_503_SERVICE_UNAVAILABLE


def test_anything_else_business_is_a_bad_request() -> None:
    assert status_for(DomainError()) == status.HTTP_400_BAD_REQUEST
