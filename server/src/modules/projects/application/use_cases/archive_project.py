"""Taking a mission out of the reference list, and putting it back."""

from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.notifications.domain.services.fan_out import notify
from src.modules.projects.application.audit import ProjectChange, trace_project_changes
from src.modules.projects.application.dtos.project_dto import (
    ArchiveProjectCommand,
    UnarchiveProjectCommand,
)
from src.modules.projects.application.use_cases.project_audience import people_on
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectCategory,
    ProjectKind,
)
from src.modules.projects.domain.repositories.project_assignee_repository import (
    ProjectAssigneeRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.services.hierarchy import (
    SubProjectPolicy,
    ensure_sub_projects_are_settled,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from src.shared.utils import clock


class ArchiveProjectUseCase:
    """Takes a mission out of the reference list, its slices with it or not.

    Archiving loses nothing: entries already booked stay readable, and only the
    list of missions one can still book against shrinks. What it cannot do
    quietly is leave the packages of an archived project behind — they would go
    on holding a rank in the plan and a card on the board on behalf of a
    project that has left. Hence the answer asked for, and refused when it is
    not given.
    """

    def __init__(
        self,
        users: UserRepository,
        projects: ProjectRepository,
        audit_logs: AuditLogRepository,
        assignees: ProjectAssigneeRepository,
        notifications: NotificationDelivery,
    ) -> None:
        self._users = users
        self._projects = projects
        self._audit_logs = audit_logs
        self._assignees = assignees
        self._notifications = notifications

    async def execute(self, command: ArchiveProjectCommand) -> Project:
        if await self._users.get_by_id(command.actor_id) is None:
            raise EntityNotFoundError("The user cannot be found.")

        project = await self._projects.get_by_id(command.project_id)
        if project is None:
            raise EntityNotFoundError("The mission cannot be found.")

        # Packages that already left are settled: the question is only about
        # the ones the archiving would leave behind.
        sub_projects = [
            package
            for package in await self._projects.list_children(command.project_id)
            if package.is_active
        ]
        ensure_sub_projects_are_settled(
            project, len(sub_projects), command.sub_projects
        )

        for package in sub_projects:
            await self._settle(package, command, inherited=project.category)

        if project.is_active:
            # Read before the mission leaves: an archived mission keeps its
            # contributors, but the line is owed to whoever was on it at the
            # moment it went.
            audience = await people_on(self._assignees, command.project_id)
            project.archive()
            await self._projects.update(project)
            await trace_project_changes(
                self._audit_logs,
                command.actor_id,
                project,
                [("is_active", True, False)],
            )
            await self._notifications.deliver(
                notify(
                    NotificationKind.PROJECT_ARCHIVED,
                    actor_id=command.actor_id,
                    recipients=audience,
                    at=clock.now(),
                    project_id=command.project_id,
                    payload={"project_label": project.label},
                )
            )

        return project

    async def _settle(
        self,
        package: Project,
        command: ArchiveProjectCommand,
        inherited: ProjectCategory | None,
    ) -> None:
        """Deals with one package, the way the gesture asked for."""
        changes: list[ProjectChange]
        if command.sub_projects is SubProjectPolicy.ARCHIVE:
            package.archive()
            changes = [("is_active", True, False)]
        else:
            # It carries on being steered, and takes over the axis it was
            # reading: what it no longer has is a project to read it from.
            changes = [
                ("kind", package.kind, ProjectKind.PROJECT),
                ("parent_id", package.parent_id, None),
                *([("category", None, inherited)] if inherited else []),
            ]
            package.detach(inherited)

        package.__post_init__()
        await self._projects.update(package)
        await trace_project_changes(
            self._audit_logs, command.actor_id, package, changes
        )


class UnarchiveProjectUseCase:
    """Puts a mission back into the reference list, forgetting when it left.

    It comes back on its own. Packages archived alongside it carry their own
    exit date and are brought back one by one: bringing back everything under
    the project would resurrect the slices that had been archived long before,
    for their own reasons.
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

    async def execute(self, command: UnarchiveProjectCommand) -> Project:
        if await self._users.get_by_id(command.actor_id) is None:
            raise EntityNotFoundError("The user cannot be found.")

        project = await self._projects.get_by_id(command.project_id)
        if project is None:
            raise EntityNotFoundError("The mission cannot be found.")

        if project.is_active:
            return project

        project.unarchive()
        await self._projects.update(project)
        await trace_project_changes(
            self._audit_logs, command.actor_id, project, [("is_active", False, True)]
        )
        return project
