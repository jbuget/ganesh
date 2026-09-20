"""Removes from a month every entry of a mission."""

from src.modules.audit_logs.domain.entities.audit_log import AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.entries.application.dtos.set_entry_dto import RemoveMissionCommand
from src.modules.entries.application.use_cases.timesheet_notice import tell_the_owner
from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.entries.domain.repositories.user_mission_repository import (
    UserMissionRepository,
)
from src.modules.months.domain.repositories.month_repository import MonthRepository
from src.modules.months.domain.services.month_period import first_day_of
from src.modules.months.domain.services.month_rules import ensure_month_is_open
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)


class RemoveMissionFromMonthUseCase:
    """Deletes a mission's row on a month, entries included.

    Removing a row from the grid erases the time it carries: the operation is
    grouped so a month never ends up half cleaned, and each entry keeps its
    trace, with its former value. The row itself goes too — otherwise a mission
    taken off would come straight back on the next reload.
    """

    def __init__(
        self,
        users: UserRepository,
        entries: EntryRepository,
        months: MonthRepository,
        audit_logs: AuditLogRepository,
        user_missions: UserMissionRepository,
        notifications: NotificationDelivery,
    ) -> None:
        self._users = users
        self._entries = entries
        self._months = months
        self._audit_logs = audit_logs
        self._user_missions = user_missions
        self._notifications = notifications

    async def execute(self, command: RemoveMissionCommand) -> float:
        """Returns how many days were removed."""
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("The user cannot be found.")
        if not actor.can_edit_open_months():
            raise ForbiddenActionError(
                "A deactivated user can no longer change an entry."
            )

        ensure_month_is_open(
            await self._months.get(command.target_user_id, command.month)
        )

        await self._user_missions.remove(
            command.target_user_id, command.project_id, command.month
        )
        # The row leaving is its own fact, said beside the entries it cleared:
        # a row taken off while empty would otherwise leave nothing at all.
        await self._audit_logs.add(
            AuditLog.month_project_remove(
                actor_id=command.actor_id,
                target_user_id=command.target_user_id,
                project_id=command.project_id,
                month=first_day_of(command.month),
            )
        )
        await tell_the_owner(
            self._notifications,
            actor_id=command.actor_id,
            owner_id=command.target_user_id,
            day=command.month,
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
