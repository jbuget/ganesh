"""Changes the phase of a project or a work package."""

from datetime import date

from src.modules.audit_logs.domain.entities.audit_log import AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.application.dtos.project_dto import ChangeProjectStatusCommand
from src.modules.projects.domain.entities.project import Project
from src.modules.projects.domain.repositories.project_detail_repository import (
    ProjectDetailRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
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
    ) -> None:
        self._users = users
        self._projects = projects
        self._details = details
        self._audit_logs = audit_logs

    async def execute(
        self, command: ChangeProjectStatusCommand, today: date | None = None
    ) -> Project:
        if await self._users.get_by_id(command.actor_id) is None:
            raise EntityNotFoundError("Utilisateur inconnu.")

        project = await self._projects.get_by_id(command.project_id)
        if project is None:
            raise EntityNotFoundError("Mission inconnue.")

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
        return project
