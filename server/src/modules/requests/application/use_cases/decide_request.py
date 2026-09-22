"""Weighs a need: accepted, refused, or not now."""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.requests.application.dtos.request_detail import RequestDetail
from src.modules.requests.application.dtos.request_dto import DecideRequestCommand
from src.modules.requests.application.use_cases.people import describe
from src.modules.requests.domain.repositories.request_repository import (
    RequestRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)
from src.shared.utils import clock


class DecideRequestUseCase:
    """Records what the team decided of a need.

    Managers alone come this far; which of them may weigh *this* need is the
    request's own business, and it turns away whoever asked for it or carries
    it.
    """

    def __init__(
        self,
        users: UserRepository,
        requests: RequestRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._users = users
        self._requests = requests
        self._audit_logs = audit_logs

    async def execute(self, command: DecideRequestCommand) -> RequestDetail:
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("The user cannot be found.")
        if not actor.can_arbitrate_requests():
            raise ForbiddenActionError("Only a manager can weigh a request.")

        request = await self._requests.get_by_id(command.request_id)
        if request is None:
            raise EntityNotFoundError("The request cannot be found.")

        now = clock.now()
        request.decide(command.decision, note=command.note, by=command.actor_id, at=now)
        await self._requests.update(request)

        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.REQUEST_DECIDE,
                actor_id=command.actor_id,
                request_id=request.id,
                new_value=request.state.value,
                # The motive travels with the line: a decision read six months
                # later without its reason is a decision one plays again.
                payload=(
                    {"note": request.decision_note}
                    if request.decision_note is not None
                    else None
                ),
                at=now,
            )
        )
        return await describe(self._users, request)
