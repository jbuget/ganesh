"""A mission's follow-up thread: post, correct, withdraw, read."""

from dataclasses import dataclass
from datetime import datetime

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.notifications.domain.services.fan_out import notify
from src.modules.projects.application.dtos.update_dto import (
    EditUpdateCommand,
    PostUpdateCommand,
    RemoveUpdateCommand,
)
from src.modules.projects.application.use_cases.project_audience import people_on
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.projects.domain.repositories.project_assignee_repository import (
    ProjectAssigneeRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.repositories.project_update_repository import (
    ProjectUpdateRepository,
)
from src.modules.projects.domain.services.mentions import mentioned_ids
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


@dataclass
class SignedUpdate:
    """An update and who wrote it."""

    update: ProjectUpdate
    author: User


class _UpdateUseCase:
    """What the three thread writes share."""

    def __init__(
        self,
        users: UserRepository,
        projects: ProjectRepository,
        updates: ProjectUpdateRepository,
        audit_logs: AuditLogRepository,
        assignees: ProjectAssigneeRepository,
        notifications: NotificationDelivery,
    ) -> None:
        self._users = users
        self._projects = projects
        self._updates = updates
        self._audit_logs = audit_logs
        self._assignees = assignees
        self._notifications = notifications

    async def _trace(
        self, action: AuditAction, actor_id: int, project_id: int, update_id: int
    ) -> None:
        await self._audit_logs.add(
            AuditLog(
                action=action,
                actor_id=actor_id,
                project_id=project_id,
                payload={"update_id": update_id},
            )
        )

    async def _load(self, update_id: int) -> ProjectUpdate:
        update = await self._updates.get(update_id)
        if update is None:
            raise EntityNotFoundError("Unknown update.")
        return update


class PostProjectUpdateUseCase(_UpdateUseCase):
    """Posts an update on a mission."""

    async def execute(
        self, command: PostUpdateCommand, now: datetime | None = None
    ) -> ProjectUpdate:
        if await self._users.get_by_id(command.actor_id) is None:
            raise EntityNotFoundError("The user cannot be found.")
        if await self._projects.get_by_id(command.project_id) is None:
            raise EntityNotFoundError("The mission cannot be found.")

        update = await self._updates.add(
            ProjectUpdate(
                id=None,
                project_id=command.project_id,
                author_id=command.actor_id,
                body=command.body,
                published_at=now or datetime.now(),
            )
        )
        assert update.id is not None
        await self._trace(
            AuditAction.UPDATE_POST, command.actor_id, command.project_id, update.id
        )
        await self._tell_the_thread(command, update)
        return update

    async def _tell_the_thread(
        self, command: PostUpdateCommand, update: ProjectUpdate
    ) -> None:
        """Who hears of an update, and under what heading.

        Being named is louder than being on the mission: someone who is both
        gets the one line that says they were spoken to, and not two. The
        mentions go out first, and the rest is told what is left.
        """
        assert update.id is not None
        named = mentioned_ids(update.body)
        payload = {"update_id": update.id}

        await self._notifications.deliver(
            notify(
                NotificationKind.UPDATE_MENTION,
                actor_id=command.actor_id,
                recipients=named,
                at=update.published_at,
                project_id=command.project_id,
                payload=payload,
            )
        )
        # Whoever is on the mission, and whoever has already spoken in the
        # thread: a question asked on a neighbouring mission deserves to hear
        # its answer.
        audience = [
            *await people_on(self._assignees, command.project_id),
            *sorted(await self._updates.authors_for_project(command.project_id)),
        ]
        await self._notifications.deliver(
            notify(
                NotificationKind.PROJECT_UPDATE_POSTED,
                actor_id=command.actor_id,
                recipients=[who for who in audience if who not in named],
                at=update.published_at,
                project_id=command.project_id,
                payload=payload,
            )
        )


class EditProjectUpdateUseCase(_UpdateUseCase):
    """Corrects an update. Author only, as the entity makes sure."""

    async def execute(
        self, command: EditUpdateCommand, now: datetime | None = None
    ) -> ProjectUpdate:
        update = await self._load(command.update_id)
        update.rewrite(command.body, by=command.actor_id, at=now or datetime.now())
        await self._updates.update(update)
        await self._trace(
            AuditAction.UPDATE_EDIT,
            command.actor_id,
            update.project_id,
            command.update_id,
        )
        return update


class RemoveProjectUpdateUseCase(_UpdateUseCase):
    """Withdraws an update. It keeps its place in the thread."""

    async def execute(
        self, command: RemoveUpdateCommand, now: datetime | None = None
    ) -> None:
        update = await self._load(command.update_id)
        update.remove(by=command.actor_id, at=now or datetime.now())
        await self._updates.update(update)
        await self._trace(
            AuditAction.UPDATE_REMOVE,
            command.actor_id,
            update.project_id,
            command.update_id,
        )


class ListProjectUpdatesUseCase:
    """A mission's thread, every update signed."""

    def __init__(self, updates: ProjectUpdateRepository, users: UserRepository) -> None:
        self._updates = updates
        self._users = users

    async def execute(self, project_id: int) -> list[SignedUpdate]:
        users = {u.id: u for u in await self._users.list_all(True)}
        return [
            SignedUpdate(update=update, author=users[update.author_id])
            for update in await self._updates.list_for_project(project_id)
            if update.author_id in users
        ]
