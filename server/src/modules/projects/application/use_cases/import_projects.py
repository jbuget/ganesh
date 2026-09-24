"""Imports a mission reference list in one pass."""

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
from src.modules.projects.domain.services.hierarchy import ensure_can_be_parent
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    DomainError,
    EntityNotFoundError,
    ForbiddenActionError,
)


class ImportProjectsUseCase:
    """Creates the missions missing from the reference list, leaving others be.

    The import can be replayed: a mission already there is skipped, never
    duplicated nor overwritten. A failing line does not stop the following
    ones, and the report says precisely what went wrong.
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
            raise EntityNotFoundError("The user cannot be found.")
        if not actor.is_manager:
            raise ForbiddenActionError("Only a manager can import a reference list.")

        report = ImportReport()
        known = {p.label: p for p in await self._projects.list_all(True)}

        for line in command.rows:
            label = line.label.strip()
            if label in known:
                report.skipped += 1
                continue
            try:
                project = await self._create(line, known)
            except DomainError as error:
                report.errors.append(f"{label or '(unnamed)'}: {error}")
                continue
            known[project.label] = project
            report.created += 1
            # One line per project, against the project itself: a single
            # summary line would live in no project's log, and opening one of
            # them nothing would say where it came from. That one import
            # created a dozen of them is read from the timestamps.
            await self._audit_logs.add(
                AuditLog(
                    action=AuditAction.PROJECT_CREATE,
                    actor_id=command.actor_id,
                    project_id=project.id,
                    new_value=project.label,
                    payload={"source": "import"},
                )
            )

        return report

    async def _create(
        self, line: ProjectImportLine, known: dict[str, Project]
    ) -> Project:
        parent_id = None
        if line.kind is ProjectKind.WORK_PACKAGE:
            parent = known.get((line.parent_label or "").strip())
            if parent is None:
                raise EntityNotFoundError(
                    f"parent project « {line.parent_label} » not found."
                )
            ensure_can_be_parent(parent, line.kind)
            parent_id = parent.id

        return await self._projects.add(
            Project(
                id=None,
                label=line.label,
                kind=line.kind,
                status=None if line.kind is ProjectKind.OFF_PROJECT else line.status,
                parent_id=parent_id,
                estimated_days=line.estimated_days,
                monday_item_id=line.monday_item_id,
                monday_subitem_id=line.monday_subitem_id,
            )
        )
