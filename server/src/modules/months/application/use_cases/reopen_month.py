"""Reopens a validated month. Managers only, and traced."""

from src.modules.audit_logs.domain.entities.audit_log import AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.months.application.dtos.month_dto import ReopenMonthCommand
from src.modules.months.domain.entities.month import Month
from src.modules.months.domain.repositories.month_repository import MonthRepository
from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.notifications.domain.services.fan_out import notify
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)
from src.shared.utils import clock


class ReopenMonthUseCase:
    """Puts a validated month back into entry."""

    def __init__(
        self,
        users: UserRepository,
        months: MonthRepository,
        audit_logs: AuditLogRepository,
        notifications: NotificationDelivery,
    ) -> None:
        self._users = users
        self._months = months
        self._audit_logs = audit_logs
        self._notifications = notifications

    async def execute(self, command: ReopenMonthCommand) -> Month:
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("The user cannot be found.")

        month = await self._months.get(command.target_user_id, command.month)
        if month is None:
            raise ForbiddenActionError("This month was never validated.")

        month.reopen(by=actor)
        await self._months.save(month)

        await self._audit_logs.add(
            AuditLog.month_reopen(
                actor_id=command.actor_id,
                target_user_id=command.target_user_id,
                month=month.month,
            )
        )
        # The owner of the month hears that somebody else settled it —
        # never that they settled it themselves.
        await self._notifications.deliver(
            notify(
                NotificationKind.MONTH_REOPENED,
                actor_id=command.actor_id,
                recipients=[command.target_user_id],
                at=clock.now(),
                day=month.month,
            )
        )
        return month
