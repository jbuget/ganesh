"""Declares or removes a contributor on a mission."""

from src.modules.audit_logs.domain.entities.audit_log import AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.application.dtos.assignment_dto import AssignmentCommand
from src.modules.projects.domain.repositories.project_assignee_repository import (
    ProjectAssigneeRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


class _AssignmentUseCase:
    """What adding and removing share: check before writing.

    Assigning someone is not an act of management: anyone may say who is about
    to step in, just as anyone may already fix a colleague's month. Only the
    existence of the mission and of the person are checked.
    """

    def __init__(
        self,
        users: UserRepository,
        projects: ProjectRepository,
        assignees: ProjectAssigneeRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._users = users
        self._projects = projects
        self._assignees = assignees
        self._audit_logs = audit_logs

    async def _ensure_both_exist(self, command: AssignmentCommand) -> None:
        if await self._projects.get_by_id(command.project_id) is None:
            raise EntityNotFoundError("The mission cannot be found.")
        if await self._users.get_by_id(command.member_id) is None:
            raise EntityNotFoundError("The user cannot be found.")


class AssignMemberUseCase(_AssignmentUseCase):
    """Declares that someone is working, or about to work, on a mission."""

    async def execute(self, command: AssignmentCommand) -> None:
        await self._ensure_both_exist(command)
        await self._assignees.assign(
            command.project_id, command.member_id, command.role
        )
        await self._audit_logs.add(
            AuditLog.project_assign(
                actor_id=command.actor_id,
                project_id=command.project_id,
                member_id=command.member_id,
                role=command.role.value,
            )
        )


class UnassignMemberUseCase(_AssignmentUseCase):
    """Removes someone from a mission's contributors."""

    async def execute(self, command: AssignmentCommand) -> None:
        await self._ensure_both_exist(command)
        await self._assignees.unassign(
            command.project_id, command.member_id, command.role
        )
        await self._audit_logs.add(
            AuditLog.project_unassign(
                actor_id=command.actor_id,
                project_id=command.project_id,
                member_id=command.member_id,
                role=command.role.value,
            )
        )
