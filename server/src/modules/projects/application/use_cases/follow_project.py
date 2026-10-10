"""Marking a mission as one the team keeps an eye on, and lowering the mark.

The mark is what the reference list and the board filter on: the missions
about to be built, being built, just delivered or just asked about. It is set
by hand and lowered by hand, one click each way, on a project or on a work
package — each says it for itself, and nothing is passed down or up.

Nothing is notified: the mark is read when somebody filters on it, and a
gesture this cheap must not interrupt anybody.
"""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.application.dtos.project_dto import FollowProjectCommand
from src.modules.projects.domain.entities.project import Project
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


class _FollowingGesture:
    """What raising and lowering the mark share: the mission, and the trace."""

    def __init__(
        self,
        users: UserRepository,
        projects: ProjectRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._users = users
        self._projects = projects
        self._audit_logs = audit_logs

    async def _load(self, command: FollowProjectCommand) -> Project:
        if await self._users.get_by_id(command.actor_id) is None:
            raise EntityNotFoundError("The user cannot be found.")
        project = await self._projects.get_by_id(command.project_id)
        if project is None:
            raise EntityNotFoundError("The mission cannot be found.")
        return project

    async def _save(
        self, command: FollowProjectCommand, project: Project, action: AuditAction
    ) -> None:
        await self._projects.update(project)
        await self._audit_logs.add(
            AuditLog(
                action=action,
                actor_id=command.actor_id,
                project_id=project.id,
            )
        )


class FollowProjectUseCase(_FollowingGesture):
    """Marks a mission as followed."""

    async def execute(self, command: FollowProjectCommand) -> Project:
        project = await self._load(command)
        if project.follow():
            await self._save(command, project, AuditAction.PROJECT_FOLLOW)
        return project


class UnfollowProjectUseCase(_FollowingGesture):
    """Lowers the mark on a mission."""

    async def execute(self, command: FollowProjectCommand) -> Project:
        project = await self._load(command)
        if project.unfollow():
            await self._save(command, project, AuditAction.PROJECT_UNFOLLOW)
        return project
