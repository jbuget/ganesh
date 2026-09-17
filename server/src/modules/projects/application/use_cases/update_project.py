"""Modifie une mission du referentiel."""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.application.dtos.project_dto import (
    ABSENT,
    UpdateProjectCommand,
)
from src.modules.projects.domain.entities.project import Project
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.services.hierarchy import ensure_can_be_parent
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError

#: Champs modifiables, dans l'ordre ou ils sont appliques.
CHAMPS = (
    "label",
    "statut",
    "estime_j",
    "categorie",
    "priorite",
    "date_mise_en_service",
    "actif",
    "parent_id",
    "monday_item_id",
    "monday_subitem_id",
)


class UpdateProjectUseCase:
    """Applique les seuls champs fournis, et trace ce qui a change.

    La modification est ouverte a toute l'equipe, comme la creation : le parti
    pris est la confiance, la tracabilite le garde-fou.
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

    async def execute(self, command: UpdateProjectCommand) -> Project:
        if await self._users.get_by_id(command.actor_id) is None:
            raise EntityNotFoundError("Utilisateur inconnu.")

        project = await self._projects.get_by_id(command.project_id)
        if project is None:
            raise EntityNotFoundError("Mission inconnue.")

        # `isinstance` ecarte a la fois ABSENT et un detachement volontaire (None).
        parent_id = command.parent_id
        if isinstance(parent_id, int):
            parent = await self._projects.get_by_id(parent_id)
            if parent is None:
                raise EntityNotFoundError("Le projet parent est introuvable.")
            ensure_can_be_parent(parent)

        changements: list[tuple[str, object, object]] = []
        for champ in CHAMPS:
            demande = getattr(command, champ)
            if demande is ABSENT:
                continue
            ancien = getattr(project, champ)
            if ancien != demande:
                changements.append((champ, ancien, demande))
                setattr(project, champ, demande)

        # Rejoue les invariants de l'entite sur l'etat resultant.
        project.__post_init__()

        await self._projects.update(project)

        for champ, ancien, nouveau in changements:
            await self._audit_logs.add(
                AuditLog(
                    action=AuditAction.PROJECT_UPDATE,
                    actor_id=command.actor_id,
                    project_id=project.id,
                    old_value=None if ancien is None else str(ancien),
                    new_value=None if nouveau is None else str(nouveau),
                    payload={"champ": champ},
                )
            )
        return project
