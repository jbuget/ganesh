"""Changes a mission in the reference list."""

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

#: Editable fields, in the order they are applied.
EDITABLE_FIELDS = (
    "label",
    "status",
    "estimated_days",
    "category",
    "priority",
    "go_live_date",
    "is_active",
    "parent_id",
    "monday_item_id",
    "monday_subitem_id",
)


class UpdateProjectUseCase:
    """Applies only the fields provided, and traces what changed.

    Editing is open to the whole team, as creation is: trust is the stance,
    traceability the safeguard.
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

        # `isinstance` rules out both ABSENT and a deliberate detach (None).
        parent_id = command.parent_id
        if isinstance(parent_id, int):
            parent = await self._projects.get_by_id(parent_id)
            if parent is None:
                raise EntityNotFoundError("The parent project cannot be found.")
            ensure_can_be_parent(parent)

        changements: list[tuple[str, object, object]] = []
        for field in EDITABLE_FIELDS:
            demande = getattr(command, field)
            if demande is ABSENT:
                continue
            ancien = getattr(project, field)
            if ancien == demande:
                continue
            changements.append((field, ancien, demande))
            if field == "is_active":
                # Leaving the reference list is dated, coming back clears the
                # date: the entity holds that rule, not the assignment.
                project.archive() if demande is False else project.unarchive()
            else:
                setattr(project, field, demande)

        # Replays the entity invariants on the resulting state.
        project.__post_init__()

        await self._projects.update(project)

        for field, ancien, new_one in changements:
            await self._audit_logs.add(
                AuditLog(
                    action=AuditAction.PROJECT_UPDATE,
                    actor_id=command.actor_id,
                    project_id=project.id,
                    old_value=None if ancien is None else str(ancien),
                    new_value=None if new_one is None else str(new_one),
                    payload={"field": field},
                )
            )
        return project
