"""Putting a tag on a mission, and taking it off.

A tag is how the team finds a mission again — by its client, its partner, its
programme, its theme — without writing another update about it. Putting one on
is one gesture: type a name, and the mission carries it. If the tag exists it
is the same one, whatever the case or the accents; if it does not it is opened
on the spot, with a colour nobody had to choose.

Nothing is notified: a gesture this cheap must not interrupt anybody. It is in
the journal, which is where a mission's history is read.
"""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.application.dtos.tag_dto import (
    TagProjectCommand,
    UntagProjectCommand,
)
from src.modules.projects.domain.entities.project import Project
from src.modules.projects.domain.entities.tag import Tag, least_used_color, tag_key
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.repositories.project_tag_repository import (
    ProjectTagRepository,
)
from src.modules.projects.domain.repositories.tag_repository import TagRepository
from src.modules.projects.domain.services.project_tagging import (
    ensure_can_carry_another,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


class _TaggingGesture:
    """What putting a tag on and taking it off share: who, which mission, and
    the trace."""

    def __init__(
        self,
        users: UserRepository,
        projects: ProjectRepository,
        tags: TagRepository,
        links: ProjectTagRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._users = users
        self._projects = projects
        self._tags = tags
        self._links = links
        self._audit_logs = audit_logs

    async def _load_project(self, actor_id: int, project_id: int) -> Project:
        if await self._users.get_by_id(actor_id) is None:
            raise EntityNotFoundError("The user cannot be found.")
        project = await self._projects.get_by_id(project_id)
        if project is None:
            raise EntityNotFoundError("The mission cannot be found.")
        return project


class TagProjectUseCase(_TaggingGesture):
    """Puts a tag on a mission, opening it if nobody had."""

    async def execute(self, command: TagProjectCommand) -> Tag:
        project = await self._load_project(command.actor_id, command.project_id)
        carried = await self._links.list_for_project(command.project_id)

        tag = await self._tags.get_by_key(tag_key(command.name))
        if tag is not None and any(c.id == tag.id for c in carried):
            return tag

        # Before the tag is opened: a refusal must not leave a tag nobody carries.
        ensure_can_carry_another(project, carried)
        if tag is None:
            tag = await self._open(command.name)

        await self._links.attach(command.project_id, tag.stored_id)
        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.PROJECT_TAG,
                actor_id=command.actor_id,
                project_id=command.project_id,
                new_value=tag.name,
                payload={"tag_id": tag.stored_id},
            )
        )
        return tag

    async def _open(self, name: str) -> Tag:
        worn = [usage.tag.color for usage in await self._tags.list_in_use()]
        return await self._tags.add(
            Tag(id=None, name=name, color=least_used_color(worn))
        )


class UntagProjectUseCase(_TaggingGesture):
    """Takes a tag off a mission."""

    async def execute(self, command: UntagProjectCommand) -> None:
        await self._load_project(command.actor_id, command.project_id)
        tag = await self._tags.get_by_id(command.tag_id)
        if tag is None:
            raise EntityNotFoundError("The tag cannot be found.")

        carried = await self._links.list_for_project(command.project_id)
        if not any(c.id == tag.id for c in carried):
            return

        await self._links.detach(command.project_id, tag.stored_id)
        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.PROJECT_UNTAG,
                actor_id=command.actor_id,
                project_id=command.project_id,
                old_value=tag.name,
                payload={"tag_id": tag.stored_id},
            )
        )
