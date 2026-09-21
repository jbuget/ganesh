"""Reading back everything that happened to one mission."""

from src.modules.audit_logs.application.dtos.audit_log_dto import AuditLogPage
from src.modules.audit_logs.application.services.signing import sign
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository


class ListProjectAuditLogUseCase:
    """A mission's log, most recent first, one page at a time.

    Everything the mission carries is read, time declared included: a log that
    sorted what deserves to be in it would no longer answer the question one
    opens it with. Length is met by paging rather than by filtering.
    """

    def __init__(self, audit_logs: AuditLogRepository, users: UserRepository) -> None:
        self._audit_logs = audit_logs
        self._users = users

    async def execute(self, project_id: int, limit: int, offset: int) -> AuditLogPage:
        logs = await self._audit_logs.list_for_project(project_id, limit, offset)
        # No mission is named on the lines: the page is the mission.
        return AuditLogPage(
            entries=await sign(logs, self._users),
            total=await self._audit_logs.count_for_project(project_id),
        )
