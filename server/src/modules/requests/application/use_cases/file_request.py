"""Opens a request."""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.requests.application.dtos.request_detail import RequestDetail
from src.modules.requests.application.dtos.request_dto import FileRequestCommand
from src.modules.requests.application.use_cases.people import describe, gather_sponsors
from src.modules.requests.domain.entities.request import Request
from src.modules.requests.domain.repositories.request_repository import (
    RequestRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository


class FileRequestUseCase:
    """Opens a need as a draft, read by nobody but whoever wrote it."""

    def __init__(
        self,
        users: UserRepository,
        requests: RequestRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._users = users
        self._requests = requests
        self._audit_logs = audit_logs

    async def execute(self, command: FileRequestCommand) -> RequestDetail:
        await gather_sponsors(self._users, command.sponsor_ids)

        request = await self._requests.add(
            Request(
                id=None,
                title=command.title,
                requester_id=command.requester_id,
                departments=command.departments,
                sponsor_ids=command.sponsor_ids,
            )
        )

        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.REQUEST_CREATE,
                actor_id=command.requester_id,
                request_id=request.id,
                new_value=request.title,
            )
        )
        return await describe(self._users, request)
