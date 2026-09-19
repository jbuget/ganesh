"""Changes a mission in the reference list."""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.application.dtos.project_dto import (
    ABSENT,
    UpdateProjectCommand,
)
from src.modules.projects.domain.entities.project import SERVICE_LINK_FIELDS, Project
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.services.hierarchy import (
    ensure_can_be_parent,
    ensure_carries_no_own_category,
    with_resolved_category,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import ConflictError, EntityNotFoundError

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
    # Service sheet.
    "slug",
    "is_published",
    "summary",
    "criticality",
    "service_type",
    "hosting",
    "has_microsoft_entra",
    "team",
    "slack_channel",
    *SERVICE_LINK_FIELDS,
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
            raise EntityNotFoundError("The user cannot be found.")

        project = await self._projects.get_by_id(command.project_id)
        if project is None:
            raise EntityNotFoundError("The mission cannot be found.")

        # `isinstance` rules out both ABSENT and a deliberate detach (None).
        parent_id = command.parent_id
        if isinstance(parent_id, int):
            parent = await self._projects.get_by_id(parent_id)
            if parent is None:
                raise EntityNotFoundError("The parent project cannot be found.")
            ensure_can_be_parent(parent)

        # A public address points at one mission: letting two claim it would
        # make the catalogue page depend on which one is read first.
        slug = command.slug
        if isinstance(slug, str):
            holder = await self._projects.get_by_slug(slug.strip().lower())
            if holder is not None and holder.id != project.id:
                raise ConflictError(f"The slug « {slug} » is already taken.")

        changes: list[tuple[str, object, object]] = []
        for field in EDITABLE_FIELDS:
            requested = getattr(command, field)
            if requested is ABSENT:
                continue
            previous = getattr(project, field)
            if previous == requested:
                continue
            changes.append((field, previous, requested))
            if field == "is_active":
                # Leaving the reference list is dated, coming back clears the
                # date: the entity holds that rule, not the assignment.
                project.archive() if requested is False else project.unarchive()
            else:
                setattr(project, field, requested)

        # Replays the entity invariants on the resulting state.
        project.__post_init__()
        ensure_carries_no_own_category(project)

        await self._projects.update(project)

        for field, previous, new_one in changes:
            await self._audit_logs.add(
                AuditLog(
                    action=AuditAction.PROJECT_UPDATE,
                    actor_id=command.actor_id,
                    project_id=project.id,
                    old_value=None if previous is None else str(previous),
                    new_value=None if new_one is None else str(new_one),
                    payload={"field": field},
                )
            )

        # A work package answers with the axis of its project, the one every
        # screen already shows it under.
        parent = (
            await self._projects.get_by_id(project.parent_id)
            if project.parent_id is not None
            else None
        )
        return with_resolved_category(project, parent)
