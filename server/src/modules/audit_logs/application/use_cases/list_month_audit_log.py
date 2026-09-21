"""Reading back one month of one person's register."""

from datetime import date

from src.modules.audit_logs.application.dtos.audit_log_dto import AuditLogPage
from src.modules.audit_logs.application.services.signing import sign
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository


class ListMonthAuditLogUseCase:
    """The life of a month, most recent first, one page at a time.

    A mission's log answers « what happened to this project », and names
    nobody's month; this one answers « what happened to my month », and names
    no person — whose month it is, the screen already says. What it does name
    is the mission each line is about, which is the one thing a declaration
    read out of its grid no longer carries.

    Nothing is sorted out here either: a validation sits beside a day booked,
    and length is met by paging.
    """

    def __init__(
        self,
        audit_logs: AuditLogRepository,
        users: UserRepository,
        projects: ProjectRepository,
    ) -> None:
        self._audit_logs = audit_logs
        self._users = users
        self._projects = projects

    async def execute(
        self, target_user_id: int, month: date, limit: int, offset: int
    ) -> AuditLogPage:
        logs = await self._audit_logs.list_for_user_month(
            target_user_id, month, limit, offset
        )
        return AuditLogPage(
            entries=await sign(logs, self._users, self._projects),
            total=await self._audit_logs.count_for_user_month(target_user_id, month),
        )
