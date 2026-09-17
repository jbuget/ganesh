"""Cree une mission dans le referentiel."""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.application.dtos.project_dto import CreateProjectCommand
from src.modules.projects.domain.entities.project import Project, ProjectKind
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.services.hierarchy import ensure_can_be_parent
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


class CreateProjectUseCase:
    """Ajoute un projet, un lot ou une activite hors projet.

    La creation est ouverte a toute l'equipe : la confiance est le parti pris,
    la tracabilite le garde-fou.
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

    async def execute(self, command: CreateProjectCommand) -> Project:
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("Utilisateur inconnu.")

        if command.kind is ProjectKind.WORK_PACKAGE:
            parent = (
                await self._projects.get_by_id(command.parent_id)
                if command.parent_id is not None
                else None
            )
            if parent is None:
                raise EntityNotFoundError("Le projet parent du lot est introuvable.")
            ensure_can_be_parent(parent)

        project = await self._projects.add(
            Project(
                id=None,
                label=command.label,
                kind=command.kind,
                status=command.status,
                parent_id=command.parent_id,
                estimated_days=command.estimated_days,
            )
        )

        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.PROJECT_CREATE,
                actor_id=command.actor_id,
                project_id=project.id,
                new_value=project.label,
            )
        )
        return project
