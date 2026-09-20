"""Changes the phase of a project or a work package."""

from datetime import date, datetime

from src.modules.audit_logs.domain.entities.audit_log import AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.notifications.domain.services.fan_out import notify
from src.modules.projects.application.dtos.project_dto import ChangeProjectStatusCommand
from src.modules.projects.application.use_cases.project_audience import people_on
from src.modules.projects.domain.entities.project import Project
from src.modules.projects.domain.repositories.project_assignee_repository import (
    ProjectAssigneeRepository,
)
from src.modules.projects.domain.repositories.project_detail_repository import (
    ProjectDetailRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.services.hierarchy import with_resolved_category
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


class ChangeProjectStatusUseCase:
    """Moves a project forward, or back, through its phases.

    The status at entry time is frozen on every `Entry`: changing the phase
    never rewrites history already consumed.
    """

    def __init__(
        self,
        users: UserRepository,
        projects: ProjectRepository,
        details: ProjectDetailRepository,
        audit_logs: AuditLogRepository,
        assignees: ProjectAssigneeRepository,
        notifications: NotificationDelivery,
    ) -> None:
        self._users = users
        self._projects = projects
        self._details = details
        self._audit_logs = audit_logs
        self._assignees = assignees
        self._notifications = notifications

    async def execute(
        self, command: ChangeProjectStatusCommand, today: date | None = None
    ) -> Project:
        if await self._users.get_by_id(command.actor_id) is None:
            raise EntityNotFoundError("The user cannot be found.")

        project = await self._projects.get_by_id(command.project_id)
        if project is None:
            raise EntityNotFoundError("The mission cannot be found.")

        previous = project.status
        project.change_status(command.status)
        await self._projects.update(project)

        # The date a phase is entered is recorded on the way through: it
        # cannot be reconstructed afterwards, and the audit log may be purged.
        await self._details.mark_phase_reached(
            command.project_id, command.status, today or date.today()
        )

        await self._audit_logs.add(
            AuditLog.project_status_change(
                actor_id=command.actor_id,
                project_id=command.project_id,
                old_status=previous.value if previous else None,
                new_status=command.status.value,
            )
        )
        # Everyone on the mission hears where it now stands. The two ends
        # travel with the line: « a fait passer en Réalisation » says more
        # than « a changé la phase ».
        await self._notifications.deliver(
            notify(
                NotificationKind.PROJECT_STATUS_CHANGED,
                actor_id=command.actor_id,
                recipients=await people_on(self._assignees, command.project_id),
                at=datetime.now(),
                project_id=command.project_id,
                payload={
                    "from": previous.value if previous else None,
                    "to": command.status.value,
                },
            )
        )

        # A work package answers with the axis of its project, the one every
        # screen already shows it under.
        parent = (
            await self._projects.get_by_id(project.parent_id)
            if project.parent_id is not None
            else None
        )
        return with_resolved_category(project, parent)
