"""Hands a need over to be weighed."""

from datetime import datetime

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.notifications.domain.entities.notification import (
    Notification,
    NotificationKind,
)
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.requests.application.dtos.request_detail import RequestDetail
from src.modules.requests.application.use_cases.people import describe
from src.modules.requests.domain.entities.request import Request
from src.modules.requests.domain.repositories.request_repository import (
    RequestRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from src.shared.utils import clock


class SubmitRequestUseCase:
    """Submits a request, and tells the managers there is one waiting."""

    def __init__(
        self,
        users: UserRepository,
        requests: RequestRepository,
        audit_logs: AuditLogRepository,
        notifications: NotificationDelivery,
    ) -> None:
        self._users = users
        self._requests = requests
        self._audit_logs = audit_logs
        self._notifications = notifications

    async def execute(self, request_id: int, actor_id: int) -> RequestDetail:
        request = await self._requests.get_by_id(request_id)
        if request is None:
            raise EntityNotFoundError("The request cannot be found.")

        now = clock.now()
        request.submit(by=actor_id, at=now)
        await self._requests.update(request)

        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.REQUEST_SUBMIT,
                actor_id=actor_id,
                request_id=request.id,
                new_value=request.title,
                at=now,
            )
        )
        await self._tell_the_managers(request, actor_id, now)
        return await describe(self._users, request)

    async def _tell_the_managers(
        self, request: Request, actor_id: int, now: datetime
    ) -> None:
        """Rings for whoever may weigh it, and never for its author.

        The title travels in the payload: the bell says what is waiting
        without the reader having to open it, and it keeps saying it should
        the request be erased.
        """
        for manager in await self._users.list_all():
            if not manager.can_arbitrate_requests() or manager.id == actor_id:
                continue
            assert manager.id is not None
            await self._notifications.deliver(
                [
                    Notification(
                        recipient_id=manager.id,
                        kind=NotificationKind.REQUEST_SUBMITTED,
                        actor_id=actor_id,
                        at=now,
                        request_id=request.id,
                        payload={"title": request.title},
                    )
                ]
            )
