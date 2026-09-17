"""Modifie les champs de fiche d'une mission."""

from dataclasses import dataclass

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.domain.entities.project import Department
from src.modules.projects.domain.entities.project_link import ProjectLink
from src.modules.projects.domain.repositories.project_detail_repository import (
    ProjectDetailRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


@dataclass(frozen=True)
class UpdateProjectDetailCommand:
    """Departements et contacts metier d'une mission."""

    actor_id: int
    project_id: int
    departements: list[Department]
    contacts_metier: str | None


@dataclass(frozen=True)
class AddLinkCommand:
    """Ajout d'un lien utile."""

    actor_id: int
    project_id: int
    label: str
    url: str


class UpdateProjectDetailUseCase:
    """Enregistre les departements et les contacts d'une mission."""

    def __init__(
        self,
        projects: ProjectRepository,
        details: ProjectDetailRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._projects = projects
        self._details = details
        self._audit_logs = audit_logs

    async def execute(self, command: UpdateProjectDetailCommand) -> None:
        mission = await self._projects.get_by_id(command.project_id)
        if mission is None:
            raise EntityNotFoundError("Mission inconnue.")

        anciens_departements = await self._details.list_departments(command.project_id)
        contacts = (command.contacts_metier or "").strip() or None
        ancien = mission.contacts_metier
        mission.contacts_metier = contacts
        await self._projects.update(mission)
        await self._details.set_departments(command.project_id, command.departements)

        # Une trace par champ, comme le fait deja la modification d'une mission.
        for champ, avant, apres in (
            ("contacts_metier", ancien, contacts),
            (
                "departements",
                ", ".join(sorted(d.value for d in anciens_departements)),
                ", ".join(sorted(d.value for d in command.departements)),
            ),
        ):
            if avant == apres:
                continue
            await self._audit_logs.add(
                AuditLog(
                    action=AuditAction.PROJECT_UPDATE,
                    actor_id=command.actor_id,
                    project_id=command.project_id,
                    old_value=avant,
                    new_value=apres,
                    payload={"champ": champ},
                )
            )


class AddProjectLinkUseCase:
    """Attache un lien utile a une mission."""

    def __init__(
        self,
        projects: ProjectRepository,
        details: ProjectDetailRepository,
    ) -> None:
        self._projects = projects
        self._details = details

    async def execute(self, command: AddLinkCommand) -> ProjectLink:
        if await self._projects.get_by_id(command.project_id) is None:
            raise EntityNotFoundError("Mission inconnue.")
        return await self._details.add_link(
            ProjectLink(
                id=None,
                project_id=command.project_id,
                label=command.label,
                url=command.url,
            )
        )


class RemoveProjectLinkUseCase:
    """Detache un lien d'une mission."""

    def __init__(self, details: ProjectDetailRepository) -> None:
        self._details = details

    async def execute(self, link_id: int) -> None:
        await self._details.remove_link(link_id)
