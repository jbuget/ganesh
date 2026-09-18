"""Changes the sheet fields of a mission."""

from dataclasses import dataclass

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.domain.entities.project import Department
from src.modules.projects.domain.entities.project_link import LinkIcon, ProjectLink
from src.modules.projects.domain.repositories.project_detail_repository import (
    ProjectDetailRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.services.link_icons import guess_icon
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


@dataclass(frozen=True)
class UpdateProjectDetailCommand:
    """Departments and business contacts of a mission."""

    actor_id: int
    project_id: int
    departments: list[Department]
    business_contacts: str | None


@dataclass(frozen=True)
class UpdateDescriptionCommand:
    """Service sheet, in markdown."""

    actor_id: int
    project_id: int
    description: str | None


@dataclass(frozen=True)
class AddLinkCommand:
    """Adding a useful link.

    The icon is optional: without an explicit choice, the address names it.
    """

    actor_id: int
    project_id: int
    label: str
    url: str
    icon: LinkIcon | None = None


class UpdateProjectDetailUseCase:
    """Saves the departments and contacts of a mission."""

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
        contacts = (command.business_contacts or "").strip() or None
        ancien = mission.business_contacts
        mission.business_contacts = contacts
        await self._projects.update(mission)
        await self._details.set_departments(command.project_id, command.departments)

        # One trace per field, as editing a mission already does.
        for field, avant, apres in (
            ("contacts_metier", ancien, contacts),
            (
                "departements",
                ", ".join(sorted(d.value for d in anciens_departements)),
                ", ".join(sorted(d.value for d in command.departments)),
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
                    payload={"field": field},
                )
            )


class AddProjectLinkUseCase:
    """Attaches a useful link to a mission."""

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
                icon=command.icon or guess_icon(command.url),
            )
        )


class RemoveProjectLinkUseCase:
    """Detaches a link from a mission."""

    def __init__(self, details: ProjectDetailRepository) -> None:
        self._details = details

    async def execute(self, link_id: int) -> None:
        await self._details.remove_link(link_id)


class UpdateDescriptionUseCase:
    """Saves the service sheet of a mission.

    The trace does not keep both versions of the text: a sheet runs to pages,
    and the audit log is there to know who touched what, not to replay
    revisions. The field name is enough.
    """

    def __init__(
        self,
        projects: ProjectRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._projects = projects
        self._audit_logs = audit_logs

    async def execute(self, command: UpdateDescriptionCommand) -> None:
        mission = await self._projects.get_by_id(command.project_id)
        if mission is None:
            raise EntityNotFoundError("Mission inconnue.")

        description = (command.description or "").strip() or None
        if description == mission.description:
            return

        mission.description = description
        await self._projects.update(mission)
        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.PROJECT_UPDATE,
                actor_id=command.actor_id,
                project_id=command.project_id,
                payload={"field": "description"},
            )
        )
