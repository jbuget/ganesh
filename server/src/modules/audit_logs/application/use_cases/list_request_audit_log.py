"""Reading back everything that happened to one need."""

from src.modules.audit_logs.application.dtos.audit_log_dto import AuditLogPage
from src.modules.audit_logs.application.services.signing import sign
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository


class ListRequestAuditLogUseCase:
    """A need's log, most recent first, one page at a time.

    Read the way a mission's is, and for the same reason: the gestures were
    traced from the first day, and a register nobody can read is not one. The
    conversion appears on both logs — its line carries the two identifiers —
    which is what ties the need to the mission it became.
    """

    def __init__(self, audit_logs: AuditLogRepository, users: UserRepository) -> None:
        self._audit_logs = audit_logs
        self._users = users

    async def execute(self, request_id: int, limit: int, offset: int) -> AuditLogPage:
        logs = await self._audit_logs.list_for_request(request_id, limit, offset)
        # No need is named on the lines: the page is the need.
        return AuditLogPage(
            entries=await sign(logs, self._users),
            total=await self._audit_logs.count_for_request(request_id),
        )
