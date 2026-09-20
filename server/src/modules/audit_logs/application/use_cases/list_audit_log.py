"""Reading back everything that happened, across the whole product."""

from datetime import datetime

from src.modules.audit_logs.application.dtos.audit_log_dto import (
    AuditLogPage,
    SignedAuditLog,
)
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository


class ListAuditLogUseCase:
    """The whole log, most recent first, one page at a time.

    A mission's « Journal » tab answers « what happened to this project ».
    This answers « what happened », with nothing left out — the question an
    archive puts, and one no screen puts.

    `since` is what makes an incremental pull possible: a reader that already
    holds everything up to a moment asks for what came after it, rather than
    paging back through a log that only ever grows.
    """

    def __init__(self, audit_logs: AuditLogRepository, users: UserRepository) -> None:
        self._audit_logs = audit_logs
        self._users = users

    async def execute(
        self, limit: int, offset: int, since: datetime | None = None
    ) -> AuditLogPage:
        logs = await self._audit_logs.list_all(limit, offset, since)
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
            total=await self._audit_logs.count_all(since),
        )
