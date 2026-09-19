"""Rearranging the reference list: what is a project, what is a slice of one."""

from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.application.audit import trace_project_changes
from src.modules.projects.application.dtos.project_dto import (
    AttachProjectCommand,
    DetachProjectCommand,
)
from src.modules.projects.domain.entities.project import Project, ProjectKind
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.services.hierarchy import (
    ensure_can_be_attached,
    ensure_can_be_detached,
    with_resolved_category,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


class AttachProjectUseCase:
    """Turns a mission into a work package of another project.

    Two projects declared apart often turn out to be two slices of one service:
    the second version of a product, its deployment work, a variant for another
    audience. Attaching says so without losing anything — the days already
    booked stay on the slice that consumed them, and the project reads their
    sum.
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

    async def execute(self, command: AttachProjectCommand) -> Project:
        if await self._users.get_by_id(command.actor_id) is None:
            raise EntityNotFoundError("The user cannot be found.")

        mission = await self._projects.get_by_id(command.project_id)
        if mission is None:
            raise EntityNotFoundError("The mission cannot be found.")

        parent = await self._projects.get_by_id(command.parent_id)
        if parent is None:
            raise EntityNotFoundError("The parent project cannot be found.")

        sub_projects = await self._projects.list_children(command.project_id)
        ensure_can_be_attached(mission, parent=parent, sub_projects=len(sub_projects))

        changes = [
            ("kind", mission.kind, ProjectKind.WORK_PACKAGE),
            ("parent_id", mission.parent_id, command.parent_id),
        ]
        mission.attach_to(command.parent_id)
        mission.__post_init__()

        await self._projects.update(mission)
        await trace_project_changes(
            self._audit_logs, command.actor_id, mission, changes
        )

        # It answers with the axis of its project, the one every screen now
        # shows it under.
        return with_resolved_category(mission, parent)


class DetachProjectUseCase:
    """Turns a work package back into a project of its own.

    The way back from attaching, and the only one: without it an aim taken at
    the wrong project could never be undone from the screens.
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

    async def execute(self, command: DetachProjectCommand) -> Project:
        if await self._users.get_by_id(command.actor_id) is None:
            raise EntityNotFoundError("The user cannot be found.")

        mission = await self._projects.get_by_id(command.project_id)
        if mission is None:
            raise EntityNotFoundError("The mission cannot be found.")

        ensure_can_be_detached(mission)

        # The axis the package was reading becomes its own: it was on that axis
        # too, and a mission coming out blank would lose what every screen
        # already showed on it.
        parent = (
            await self._projects.get_by_id(mission.parent_id)
            if mission.parent_id is not None
            else None
        )
        inherited = parent.category if parent else None

        changes = [
            ("kind", mission.kind, ProjectKind.PROJECT),
            ("parent_id", mission.parent_id, None),
            *([("category", None, inherited)] if inherited else []),
        ]
        mission.detach(inherited)
        mission.__post_init__()

        await self._projects.update(mission)
        await trace_project_changes(
            self._audit_logs, command.actor_id, mission, changes
        )

        return mission
