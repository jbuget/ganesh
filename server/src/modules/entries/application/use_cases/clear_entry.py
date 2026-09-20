"""Removes a time entry."""

from src.modules.audit_logs.domain.entities.audit_log import AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.entries.application.dtos.set_entry_dto import ClearEntryCommand
from src.modules.entries.application.use_cases.timesheet_notice import tell_the_owner
from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.months.domain.repositories.month_repository import MonthRepository
from src.modules.months.domain.services.month_rules import ensure_month_is_open
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)


class ClearEntryUseCase:
    """Deletes an entry, if the month allows it.

    Unlike writing, deleting stays allowed on a non-working day: forbidding
    entry there must not prevent cleaning up inherited or imported data.
    """

    def __init__(
        self,
        users: UserRepository,
        entries: EntryRepository,
        months: MonthRepository,
        audit_logs: AuditLogRepository,
        notifications: NotificationDelivery,
    ) -> None:
        self._users = users
        self._entries = entries
        self._months = months
        self._audit_logs = audit_logs
        self._notifications = notifications

    async def execute(self, command: ClearEntryCommand) -> None:
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("The user cannot be found.")
        if not actor.can_edit_open_months():
            raise ForbiddenActionError(
                "A deactivated user can no longer change an entry."
            )

        ensure_month_is_open(
            await self._months.get(command.target_user_id, command.day)
        )

        existing = await self._entries.get(
            command.target_user_id, command.project_id, command.day
        )
        if existing is None:
            # The entry cycle passes through empty: finding nothing is normal.
            return

        await self._entries.delete(
            command.target_user_id, command.project_id, command.day
        )
        await self._audit_logs.add(
            AuditLog.entry_clear(
                actor_id=command.actor_id,
                target_user_id=command.target_user_id,
                project_id=command.project_id,
                day=command.day,
                old_value=float(existing.value),
            )
        )
        await tell_the_owner(
            self._notifications,
            actor_id=command.actor_id,
            owner_id=command.target_user_id,
            day=command.day,
        )
