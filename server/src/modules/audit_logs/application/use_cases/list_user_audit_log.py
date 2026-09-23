"""Reading back everything one teammate's id appears on."""

from src.modules.audit_logs.application.dtos.audit_log_dto import AuditLogPage
from src.modules.audit_logs.application.services.signing import sign
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository


class ListUserAuditLogUseCase:
    """One person's log, most recent first, one page at a time.

    A mission's log reads back everything carrying its `project_id`; this
    reads back everything carrying one person's, on either side of it. What
    they did and what was done to them sit together on purpose: a panel that
    showed only their own gestures would leave out the day their role was
    changed, and one that showed only the changes made to them would leave out
    the month they filled in for a colleague. Both are what somebody opening
    the panel came to find.

    Nothing is sorted out, as nowhere else it is: time declared sits beside a
    project archived, and length is met by paging.

    Every line names its mission, as the register read across does: the panel
    is a person, not a project, and « a ajouté un fichier » with no mission
    beside it names a gesture nobody can place.
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

    async def execute(self, user_id: int, limit: int, offset: int) -> AuditLogPage:
        logs = await self._audit_logs.list_for_user(user_id, limit, offset)
        return AuditLogPage(
            entries=await sign(logs, self._users, self._projects),
            total=await self._audit_logs.count_for_user(user_id),
        )
