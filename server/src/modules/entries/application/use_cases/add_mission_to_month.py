"""Puts a mission on a month, ahead of any time entered on it."""

from src.modules.audit_logs.domain.entities.audit_log import AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.entries.application.dtos.set_entry_dto import AddMissionCommand
from src.modules.entries.domain.repositories.user_mission_repository import (
    UserMissionRepository,
)
from src.modules.months.domain.repositories.month_repository import MonthRepository
from src.modules.months.domain.services.month_period import first_day_of
from src.modules.months.domain.services.month_rules import ensure_month_is_open
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)


class AddMissionToMonthUseCase:
    """Records that a mission belongs to a month, with nothing on it yet.

    Preparing one's month — lining up what one is about to work on — is a
    gesture of its own, and the grid must still show it after a reload. No time
    is written: the row stays empty until someone enters a day on it.
    """

    def __init__(
        self,
        users: UserRepository,
        projects: ProjectRepository,
        months: MonthRepository,
        user_missions: UserMissionRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._users = users
        self._projects = projects
        self._months = months
        self._user_missions = user_missions
        self._audit_logs = audit_logs

    async def execute(self, command: AddMissionCommand) -> None:
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("The user cannot be found.")
        if not actor.can_edit_open_months():
            raise ForbiddenActionError(
                "A deactivated user can no longer change a month."
            )

        if await self._users.get_by_id(command.target_user_id) is None:
            raise EntityNotFoundError("The target user cannot be found.")

        if await self._projects.get_by_id(command.project_id) is None:
            raise EntityNotFoundError("The mission cannot be found.")

        ensure_month_is_open(
            await self._months.get(command.target_user_id, command.month)
        )

        await self._user_missions.add(
            command.target_user_id, command.project_id, command.month
        )
        await self._audit_logs.add(
            AuditLog.month_project_add(
                actor_id=command.actor_id,
                target_user_id=command.target_user_id,
                project_id=command.project_id,
                month=first_day_of(command.month),
            )
        )
