"""Locks a month of entries."""

from src.modules.audit_logs.domain.entities.audit_log import AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.months.application.dtos.month_dto import ValidateMonthCommand
from src.modules.months.domain.entities.month import Month
from src.modules.months.domain.repositories.month_repository import MonthRepository
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)


class ValidateMonthUseCase:
    """Moves a month to the validated state, once the user confirms."""

    def __init__(
        self,
        users: UserRepository,
        months: MonthRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._users = users
        self._months = months
        self._audit_logs = audit_logs

    async def execute(self, command: ValidateMonthCommand) -> Month:
        if command.actor_id != command.target_user_id:
            raise ForbiddenActionError(
                "Everyone validates their own month: validation cannot be delegated."
            )

        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("Utilisateur inconnu.")

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
        return month
