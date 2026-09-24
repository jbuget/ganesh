"""Turning business errors into HTTP responses.

The presentation layer alone knows HTTP: the domain raises business
exceptions, without ever knowing how they will be rendered.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.shared.exceptions.domain_exceptions import (
    ConflictError,
    DomainError,
    EntityNotFoundError,
    ForbiddenActionError,
    ServiceUnavailableError,
    ValidationError,
)

STATUS_BY_ERROR: dict[type[Exception], int] = {
    EntityNotFoundError: status.HTTP_404_NOT_FOUND,
    ValidationError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    ForbiddenActionError: status.HTTP_403_FORBIDDEN,
    ConflictError: status.HTTP_409_CONFLICT,
    ServiceUnavailableError: status.HTTP_503_SERVICE_UNAVAILABLE,
}


def status_for(error: Exception) -> int:
    """The status a business error answers with, its parents included.

    Walked rather than looked up on the exact type: a module that narrows one
    of these — `MailerUnavailableError` under `ServiceUnavailableError` — means the
    same thing more precisely, and would otherwise fall through to 400 and
    send the caller looking at their own request.
    """
    for klass in type(error).__mro__:
        if klass in STATUS_BY_ERROR:
            return STATUS_BY_ERROR[klass]
    return status.HTTP_400_BAD_REQUEST


def register_domain_exception_handlers(app: FastAPI) -> None:
    """Wires business exceptions to their HTTP status codes."""

    async def handle(request: Request, error: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status_for(error), content={"detail": str(error)}
        )

    for error_type in (*STATUS_BY_ERROR, DomainError):
        app.add_exception_handler(error_type, handle)
