"""Erases a draft."""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.requests.domain.repositories.request_repository import (
    RequestRepository,
)
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)


class DeleteRequestUseCase:
    """Erases a draft, its author's alone.

    The line of log survives it, pointing at a request that is no longer
    there: what was opened and erased the same morning leaves that much, and
    no more.
    """

    def __init__(
        self, requests: RequestRepository, audit_logs: AuditLogRepository
    ) -> None:
        self._requests = requests
        self._audit_logs = audit_logs

    async def execute(self, request_id: int, actor_id: int) -> None:
        request = await self._requests.get_by_id(request_id)
        if request is None:
            raise EntityNotFoundError("The request cannot be found.")
        if not request.may_be_deleted_by(actor_id):
            raise ForbiddenActionError(
                "Only a draft is erased, and only by whoever wrote it."
            )

        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.REQUEST_DELETE,
                actor_id=actor_id,
                request_id=request.id,
                old_value=request.title,
            )
        )
        await self._requests.delete(request_id)
