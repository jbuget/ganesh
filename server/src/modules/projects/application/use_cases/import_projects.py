"""Importe un referentiel de missions en une passe."""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.application.dtos.project_dto import (
    ImportProjectsCommand,
    ImportReport,
    ProjectImportLine,
)
from src.modules.projects.domain.entities.project import Project, ProjectKind
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    DomainError,
    EntityNotFoundError,
    ForbiddenActionError,
)


class ImportProjectsUseCase:
    """Cree les missions absentes du referentiel, sans toucher aux autres.

    L'import est rejouable : une mission deja presente est ignoree, jamais
    dupliquee ni ecrasee. Une ligne en erreur n'interrompt pas les suivantes,
    et le rapport dit precisement ce qui a echoue.
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

    async def execute(self, command: ImportProjectsCommand) -> ImportReport:
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("Utilisateur inconnu.")
        if not actor.is_manager:
            raise ForbiddenActionError("Seul un manager peut importer un referentiel.")

        rapport = ImportReport()
        connus = {p.label: p for p in await self._projects.list_all(True)}

        for ligne in command.lignes:
            label = ligne.label.strip()
            if label in connus:
                rapport.ignores += 1
                continue
            try:
                projet = await self._creer(ligne, connus)
            except DomainError as erreur:
                rapport.erreurs.append(f"{label or '(sans nom)'} : {erreur}")
                continue
            connus[projet.label] = projet
            rapport.crees += 1

        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.PROJECT_CREATE,
                actor_id=command.actor_id,
                new_value=f"import : {rapport.crees} mission(s)",
            )
        )
        return rapport

    async def _creer(
        self, ligne: ProjectImportLine, connus: dict[str, Project]
    ) -> Project:
        parent_id = None
        if ligne.kind is ProjectKind.LOT:
            parent = connus.get((ligne.parent_label or "").strip())
            if parent is None:
                raise EntityNotFoundError(
                    f"projet parent « {ligne.parent_label} » introuvable."
                )
            parent_id = parent.id

        return await self._projects.add(
            Project(
                id=None,
                label=ligne.label,
                kind=ligne.kind,
                statut=None if ligne.kind is ProjectKind.HORS_PROJET else ligne.statut,
                parent_id=parent_id,
                estime_j=ligne.estime_j,
                monday_item_id=ligne.monday_item_id,
                monday_subitem_id=ligne.monday_subitem_id,
            )
        )
