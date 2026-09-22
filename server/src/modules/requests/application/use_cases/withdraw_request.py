"""Takes a request back to the drawing board."""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.requests.application.dtos.request_detail import RequestDetail
from src.modules.requests.application.use_cases.people import describe
from src.modules.requests.domain.repositories.request_repository import (
    RequestRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


class WithdrawRequestUseCase:
    """Puts a submitted request back into its author's hands."""

    def __init__(
        self,
        users: UserRepository,
        requests: RequestRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._users = users
        self._requests = requests
        self._audit_logs = audit_logs

    async def execute(self, request_id: int, actor_id: int) -> RequestDetail:
        request = await self._requests.get_by_id(request_id)
        if request is None:
            raise EntityNotFoundError("The request cannot be found.")

        request.withdraw(by=actor_id)
        await self._requests.update(request)

        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.REQUEST_WITHDRAW,
                actor_id=actor_id,
                request_id=request.id,
                new_value=request.title,
            )
        )
        return await describe(self._users, request)
