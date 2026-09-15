"""Change la phase d'un projet ou d'un lot."""

from src.modules.audit_logs.domain.entities.audit_log import AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.application.dtos.project_dto import ChangeProjectStatusCommand
from src.modules.projects.domain.entities.project import Project
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


class ChangeProjectStatusUseCase:
    """Fait avancer, ou reculer, un projet dans ses phases.

    Le statut au moment de la saisie est fige sur chaque `Entry` : changer la
    phase ne reecrit jamais l'historique deja consomme.
    """

    def __init__(
        self,
        users: UserRepository,
        projects: ProjectRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._users = users
        self._projects = projects
        self._audit_logs = audit_logs

    async def execute(self, command: ChangeProjectStatusCommand) -> Project:
        if await self._users.get_by_id(command.actor_id) is None:
            raise EntityNotFoundError("Utilisateur inconnu.")

        project = await self._projects.get_by_id(command.project_id)
        if project is None:
            raise EntityNotFoundError("Mission inconnue.")

        previous = project.statut
        project.change_status(command.statut)
        await self._projects.update(project)

        await self._audit_logs.add(
            AuditLog.project_status_change(
                actor_id=command.actor_id,
                project_id=command.project_id,
                old_status=previous.value if previous else None,
                new_status=command.statut.value,
            )
        )
        return project
