"""Changes the sheet fields of a mission."""

from dataclasses import dataclass

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.domain.entities.project_link import LinkIcon, ProjectLink
from src.modules.projects.domain.repositories.project_detail_repository import (
    ProjectDetailRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.services.link_icons import guess_icon
from src.shared.enums.department import Department
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
            raise EntityNotFoundError("The mission cannot be found.")

        previous_departments = await self._details.list_departments(command.project_id)
        contacts = (command.business_contacts or "").strip() or None
        previous = mission.business_contacts
        mission.business_contacts = contacts
        await self._projects.update(mission)
        await self._details.set_departments(command.project_id, command.departments)

        # One trace per field, as editing a mission already does.
        for field, before, after in (
            ("business_contacts", previous, contacts),
            (
                "departments",
                ", ".join(sorted(d.value for d in previous_departments)),
                ", ".join(sorted(d.value for d in command.departments)),
            ),
        ):
            if before == after:
                continue
            await self._audit_logs.add(
                AuditLog(
                    action=AuditAction.PROJECT_UPDATE,
                    actor_id=command.actor_id,
                    project_id=command.project_id,
                    old_value=before,
                    new_value=after,
                    payload={"field": field},
                )
            )


async def _trace_link(
    audit_logs: AuditLogRepository,
    actor_id: int,
    project_id: int,
    attached: str | None,
    detached: str | None,
) -> None:
    """Records a link coming or going, as the rest of the sheet is recorded.

    Under the same field as the sheet's other lists: what one reads back is a
    project whose links changed, which is exactly what happened. The name is
    kept rather than the address: it is what the screen showed, and what a
    reader recognises the link by.
    """
    await audit_logs.add(
        AuditLog(
            action=AuditAction.PROJECT_UPDATE,
            actor_id=actor_id,
            project_id=project_id,
            old_value=detached,
            new_value=attached,
            payload={"field": "links"},
        )
    )


class AddProjectLinkUseCase:
    """Attaches a useful link to a mission."""

    def __init__(
        self,
        projects: ProjectRepository,
        details: ProjectDetailRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._projects = projects
        self._details = details
        self._audit_logs = audit_logs

    async def execute(self, command: AddLinkCommand) -> ProjectLink:
        if await self._projects.get_by_id(command.project_id) is None:
            raise EntityNotFoundError("The mission cannot be found.")
        link = await self._details.add_link(
            ProjectLink(
                id=None,
                project_id=command.project_id,
                label=command.label,
                url=command.url,
                icon=command.icon or guess_icon(command.url),
            )
        )
        await _trace_link(
            self._audit_logs,
            command.actor_id,
            command.project_id,
            attached=link.label,
            detached=None,
        )
        return link


class RemoveProjectLinkUseCase:
    """Detaches a link from a mission."""

    def __init__(
        self,
        details: ProjectDetailRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._details = details
        self._audit_logs = audit_logs

    async def execute(self, link_id: int, actor_id: int) -> None:
        # Read before it goes: afterwards there is no way to say which project
        # it hung on, nor under what name.
        link = await self._details.get_link(link_id)
        if link is None:
            return
        await self._details.remove_link(link_id)
        await _trace_link(
            self._audit_logs,
            actor_id,
            link.project_id,
            attached=None,
            detached=link.label,
        )


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
            raise EntityNotFoundError("The mission cannot be found.")

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
