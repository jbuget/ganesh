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
    ValidationError,
)

STATUS_BY_ERROR: dict[type[Exception], int] = {
    EntityNotFoundError: status.HTTP_404_NOT_FOUND,
    ValidationError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    ForbiddenActionError: status.HTTP_403_FORBIDDEN,
    ConflictError: status.HTTP_409_CONFLICT,
}


def register_domain_exception_handlers(app: FastAPI) -> None:
    """Wires business exceptions to their HTTP status codes."""

    async def handle(request: Request, error: Exception) -> JSONResponse:
        http_status = STATUS_BY_ERROR.get(type(error), status.HTTP_400_BAD_REQUEST)
        return JSONResponse(status_code=http_status, content={"detail": str(error)})

    for error_type in (*STATUS_BY_ERROR, DomainError):
        app.add_exception_handler(error_type, handle)
