"""Toutes les exceptions metier derivent de DomainError."""

import pytest

from src.shared.exceptions.domain_exceptions import (
    ConflictError,
    DomainError,
    EntityNotFoundError,
    ForbiddenActionError,
    ValidationError,
)


@pytest.mark.parametrize(
    "exception_class",
    [EntityNotFoundError, ValidationError, ForbiddenActionError, ConflictError],
)
def test_business_exception_derives_from_domain_error(
    exception_class: type[DomainError],
) -> None:
    assert issubclass(exception_class, DomainError)
