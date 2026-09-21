"""Reading back everything that happened, across the whole product."""

from datetime import datetime

from src.modules.audit_logs.application.dtos.audit_log_dto import AuditLogPage
from src.modules.audit_logs.application.services.signing import sign
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
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
        return AuditLogPage(
            entries=await sign(logs, self._users),
            total=await self._audit_logs.count_all(since),
        )
