"""Deletes a mission that was never used."""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.notifications.domain.services.fan_out import notify
from src.modules.projects.application.dtos.project_dto import DeleteProjectCommand
from src.modules.projects.application.use_cases.project_audience import people_on
from src.modules.projects.domain.repositories.project_assignee_repository import (
    ProjectAssigneeRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.services.deletion import ensure_can_be_deleted
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from src.shared.utils import clock


class DeleteProjectUseCase:
    """Takes a mission that never served out of the reference list.

    As soon as a mission carries time, deletion is refused in favour of
    archiving: the reference list is tidied without ever losing a declaration.
    """

    def __init__(
        self,
        users: UserRepository,
        projects: ProjectRepository,
        entries: EntryRepository,
        audit_logs: AuditLogRepository,
        assignees: ProjectAssigneeRepository,
        notifications: NotificationDelivery,
    ) -> None:
        self._users = users
        self._projects = projects
        self._entries = entries
        self._audit_logs = audit_logs
        self._assignees = assignees
        self._notifications = notifications

    async def execute(self, command: DeleteProjectCommand) -> None:
        if await self._users.get_by_id(command.actor_id) is None:
            raise EntityNotFoundError("The user cannot be found.")

        project = await self._projects.get_by_id(command.project_id)
        if project is None:
            raise EntityNotFoundError("The mission cannot be found.")

        entries = (await self._entries.count_by_project()).get(command.project_id, 0)
        sub_projects = len(await self._projects.list_children(command.project_id))
        ensure_can_be_deleted(project, entries=entries, sub_projects=sub_projects)

        # Read before the row goes: once deleted, nothing says who was on it.
        audience = await people_on(self._assignees, command.project_id)

        await self._projects.delete(command.project_id)
        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.PROJECT_DELETE,
                actor_id=command.actor_id,
                project_id=None,
                old_value=project.label,
            )
        )
        # The mission is gone, so its name travels with the line: there is
        # nothing left to read it from.
        await self._notifications.deliver(
            notify(
                NotificationKind.PROJECT_DELETED,
                actor_id=command.actor_id,
                recipients=audience,
                at=clock.now(),
                payload={"project_label": project.label},
            )
        )
