"""Reading back everything that happened to one mission."""

from src.modules.audit_logs.application.dtos.audit_log_dto import (
    AuditLogPage,
    SignedAuditLog,
)
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.users.domain.entities.user import User
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
        # Deactivated people keep signing what they did while they were there.
        people: dict[int, User] = {
            person.id: person
            for person in await self._users.list_all(include_inactive=True)
            if person.id is not None
        }
        return AuditLogPage(
            entries=[
                SignedAuditLog(
                    log=log,
                    actor=people.get(log.actor_id),
                    target_user=(
                        None
                        if log.target_user_id is None
                        else people.get(log.target_user_id)
                    ),
                )
                for log in logs
            ],
            total=await self._audit_logs.count_for_project(project_id),
        )
