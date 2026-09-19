"""Puts a mission on a month, ahead of any time entered on it."""

from src.modules.entries.application.dtos.set_entry_dto import AddMissionCommand
from src.modules.entries.domain.repositories.user_mission_repository import (
    UserMissionRepository,
)
from src.modules.months.domain.repositories.month_repository import MonthRepository
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
    ) -> None:
        self._users = users
        self._projects = projects
        self._months = months
        self._user_missions = user_missions

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

        month = command.month.replace(day=1)
        month_status = await self._months.get(command.target_user_id, month)
        if month_status is not None and not month_status.is_writable:
            raise ForbiddenActionError(
                "This month is validated: a manager must reopen it."
            )

        await self._user_missions.add(command.target_user_id, command.project_id, month)
