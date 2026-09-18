"""Removes from a month every entry of a mission."""

from src.modules.audit_logs.domain.entities.audit_log import AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.entries.application.dtos.set_entry_dto import RemoveMissionCommand
from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.months.domain.repositories.month_repository import MonthRepository
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)


class RemoveMissionFromMonthUseCase:
    """Deletes a mission's row on a month, entries included.

    Removing a row from the grid erases the time it carries: the operation is
    grouped so a month never ends up half cleaned, and each entry keeps its
    trace, with its former value.
    """

    def __init__(
        self,
        users: UserRepository,
        entries: EntryRepository,
        months: MonthRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._users = users
        self._entries = entries
        self._months = months
        self._audit_logs = audit_logs

    async def execute(self, command: RemoveMissionCommand) -> float:
        """Returns how many days were removed."""
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("Utilisateur inconnu.")
        if not actor.can_edit_open_months():
            raise ForbiddenActionError(
                "A deactivated user can no longer change an entry."
            )

        month = await self._months.get(command.target_user_id, command.month)
        if month is not None and not month.is_writable:
            raise ForbiddenActionError(
                "This month is validated: a manager must reopen it."
            )

        entries = [
            entry
            for entry in await self._entries.list_for_month(
                command.target_user_id, command.month
            )
            if entry.project_id == command.project_id
        ]

        removed = 0.0
        for entry in entries:
            await self._entries.delete(
                command.target_user_id, command.project_id, entry.day
            )
            await self._audit_logs.add(
                AuditLog.entry_clear(
                    actor_id=command.actor_id,
                    target_user_id=command.target_user_id,
                    project_id=command.project_id,
                    day=entry.day,
                    old_value=float(entry.value),
                )
            )
            removed += float(entry.value)
        return removed
