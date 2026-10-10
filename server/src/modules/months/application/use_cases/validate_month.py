"""Locks a month of entries."""

from src.modules.audit_logs.domain.entities.audit_log import AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.months.application.dtos.month_dto import ValidateMonthCommand
from src.modules.months.domain.entities.month import Month
from src.modules.months.domain.repositories.month_repository import MonthRepository
from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.notifications.domain.services.fan_out import notify
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from src.shared.utils import clock


class ValidateMonthUseCase:
    """Moves a month to the validated state, once its owner or a manager confirms."""

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

    async def execute(self, command: ValidateMonthCommand) -> Month:
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("The user cannot be found.")
        if await self._users.get_by_id(command.target_user_id) is None:
            raise EntityNotFoundError("The user cannot be found.")

        month = await self._months.get(command.target_user_id, command.month)
        if month is None:
            month = Month(user_id=command.target_user_id, month=command.month)

        month.validate(by=actor)
        await self._months.save(month)

        await self._audit_logs.add(
            AuditLog.month_validate(
                actor_id=command.actor_id,
                target_user_id=command.target_user_id,
                month=month.month,
            )
        )
        # The owner hears that somebody else settled it — never that they
        # settled it themselves, which `notify` leaves out.
        await self._notifications.deliver(
            notify(
                NotificationKind.MONTH_VALIDATED,
                actor_id=command.actor_id,
                recipients=[command.target_user_id],
                at=clock.now(),
                day=month.month,
            )
        )
        return month
