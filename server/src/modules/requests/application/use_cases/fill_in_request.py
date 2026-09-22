"""Writes the sheet of a request."""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.requests.application.dtos.request_detail import RequestDetail
from src.modules.requests.application.dtos.request_dto import FillInRequestCommand
from src.modules.requests.application.use_cases.people import describe, gather_sponsors
from src.modules.requests.domain.repositories.request_repository import (
    RequestRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


class FillInRequestUseCase:
    """Rewrites what a draft says. Its author alone, and only while it is one."""

    def __init__(
        self,
        users: UserRepository,
        requests: RequestRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._users = users
        self._requests = requests
        self._audit_logs = audit_logs

    async def execute(self, command: FillInRequestCommand) -> RequestDetail:
        request = await self._requests.get_by_id(command.request_id)
        if request is None:
            raise EntityNotFoundError("The request cannot be found.")

        await gather_sponsors(self._users, command.sponsor_ids)

        request.fill_in(
            title=command.title,
            departments=command.departments,
            sponsor_ids=command.sponsor_ids,
            problem=command.problem,
            impact=command.impact,
            expected_outcome=command.expected_outcome,
            cost_of_inaction=command.cost_of_inaction,
            desired_by=command.desired_by,
            envisaged_solution=command.envisaged_solution,
            by=command.actor_id,
        )
        await self._requests.update(request)

        # The sheet is written whole, so the trace says it was rewritten and
        # not which of eight fields moved: the panel saves as one types, and a
        # line per keystroke would bury the day it was submitted.
        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.REQUEST_UPDATE,
                actor_id=command.actor_id,
                request_id=request.id,
                new_value=request.title,
            )
        )
        return await describe(self._users, request)
