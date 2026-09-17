"""Le fil de suivi d'une mission : publier, corriger, retirer, lire."""

from dataclasses import dataclass
from datetime import datetime

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.application.dtos.update_dto import (
    EditUpdateCommand,
    PostUpdateCommand,
    RemoveUpdateCommand,
)
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.repositories.project_update_repository import (
    ProjectUpdateRepository,
)
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


@dataclass
class SignedUpdate:
    """Une mise a jour et qui l'a ecrite."""

    update: ProjectUpdate
    author: User


class _UpdateUseCase:
    """Ce que partagent les trois ecritures du fil."""

    def __init__(
        self,
        users: UserRepository,
        projects: ProjectRepository,
        updates: ProjectUpdateRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._users = users
        self._projects = projects
        self._updates = updates
        self._audit_logs = audit_logs

    async def _tracer(
        self, action: AuditAction, actor_id: int, project_id: int, update_id: int
    ) -> None:
        await self._audit_logs.add(
            AuditLog(
                action=action,
                actor_id=actor_id,
                project_id=project_id,
                payload={"update_id": update_id},
            )
        )

    async def _charger(self, update_id: int) -> ProjectUpdate:
        maj = await self._updates.get(update_id)
        if maj is None:
            raise EntityNotFoundError("Mise a jour inconnue.")
        return maj


class PostProjectUpdateUseCase(_UpdateUseCase):
    """Publie une mise a jour sur une mission."""

    async def execute(
        self, command: PostUpdateCommand, now: datetime | None = None
    ) -> ProjectUpdate:
        if await self._users.get_by_id(command.actor_id) is None:
            raise EntityNotFoundError("Utilisateur inconnu.")
        if await self._projects.get_by_id(command.project_id) is None:
            raise EntityNotFoundError("Mission inconnue.")

        maj = await self._updates.add(
            ProjectUpdate(
                id=None,
                project_id=command.project_id,
                author_id=command.actor_id,
                texte=command.texte,
                publiee_le=now or datetime.now(),
            )
        )
        assert maj.id is not None
        await self._tracer(
            AuditAction.UPDATE_POST, command.actor_id, command.project_id, maj.id
        )
        return maj


class EditProjectUpdateUseCase(_UpdateUseCase):
    """Corrige une mise a jour. Reserve a son auteur, l'entite s'en assure."""

    async def execute(
        self, command: EditUpdateCommand, now: datetime | None = None
    ) -> ProjectUpdate:
        maj = await self._charger(command.update_id)
        maj.reecrire(command.texte, par=command.actor_id, a=now or datetime.now())
        await self._updates.update(maj)
        await self._tracer(
            AuditAction.UPDATE_EDIT, command.actor_id, maj.project_id, command.update_id
        )
        return maj


class RemoveProjectUpdateUseCase(_UpdateUseCase):
    """Retire une mise a jour. Elle garde sa place dans le fil."""

    async def execute(
        self, command: RemoveUpdateCommand, now: datetime | None = None
    ) -> None:
        maj = await self._charger(command.update_id)
        maj.supprimer(par=command.actor_id, a=now or datetime.now())
        await self._updates.update(maj)
        await self._tracer(
            AuditAction.UPDATE_REMOVE,
            command.actor_id,
            maj.project_id,
            command.update_id,
        )


class ListProjectUpdatesUseCase:
    """Le fil d'une mission, chaque mise a jour signee."""

    def __init__(self, updates: ProjectUpdateRepository, users: UserRepository) -> None:
        self._updates = updates
        self._users = users

    async def execute(self, project_id: int) -> list[SignedUpdate]:
        utilisateurs = {u.id: u for u in await self._users.list_all(True)}
        return [
            SignedUpdate(update=maj, author=utilisateurs[maj.author_id])
            for maj in await self._updates.list_for_project(project_id)
            if maj.author_id in utilisateurs
        ]
