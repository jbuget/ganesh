"""The files of a mission: drop one, read them back, take one away."""

from dataclasses import dataclass
from datetime import datetime

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.application.dtos.attachment_dto import (
    RemoveAttachmentCommand,
    UploadAttachmentCommand,
)
from src.modules.projects.domain.entities.project_attachment import ProjectAttachment
from src.modules.projects.domain.repositories.attachment_store import AttachmentStore
from src.modules.projects.domain.repositories.project_attachment_repository import (
    ProjectAttachmentRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.repositories.project_update_repository import (
    ProjectUpdateRepository,
)
from src.modules.projects.domain.services.attachment_references import referenced_ids
from src.modules.projects.domain.services.storage_keys import key_for
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from src.shared.utils import clock


@dataclass
class SignedAttachment:
    """A file, who dropped it, and how many updates would lose it."""

    attachment: ProjectAttachment
    uploader: User
    used_in_updates: int


class _AttachmentUseCase:
    """What the two writes share."""

    def __init__(
        self,
        users: UserRepository,
        projects: ProjectRepository,
        attachments: ProjectAttachmentRepository,
        store: AttachmentStore,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._users = users
        self._projects = projects
        self._attachments = attachments
        self._store = store
        self._audit_logs = audit_logs

    async def _trace(
        self,
        action: AuditAction,
        actor_id: int,
        attachment: ProjectAttachment,
    ) -> None:
        # The name travels on the line rather than being read back from the
        # file: by the time the Journal is opened, the file may be gone.
        await self._audit_logs.add(
            AuditLog(
                action=action,
                actor_id=actor_id,
                project_id=attachment.project_id,
                payload={
                    "attachment_id": attachment.id,
                    "filename": attachment.filename,
                },
            )
        )


class UploadProjectAttachmentUseCase(_AttachmentUseCase):
    """Drops a file on a mission."""

    async def execute(
        self, command: UploadAttachmentCommand, now: datetime | None = None
    ) -> ProjectAttachment:
        if await self._users.get_by_id(command.actor_id) is None:
            raise EntityNotFoundError("The user cannot be found.")
        if await self._projects.get_by_id(command.project_id) is None:
            raise EntityNotFoundError("The mission cannot be found.")

        # Built before anything is written: the entity carries the limit, and
        # a file it refuses must not have reached the store first.
        attachment = ProjectAttachment(
            id=None,
            project_id=command.project_id,
            uploaded_by=command.actor_id,
            filename=command.filename,
            content_type=command.content_type,
            size_bytes=len(command.content),
            storage_key=key_for(command.project_id, command.filename),
            uploaded_at=now or clock.now(),
        )

        await self._store.put(
            attachment.storage_key, command.content, attachment.content_type
        )
        stored = await self._attachments.add(attachment)
        await self._trace(AuditAction.ATTACHMENT_ADD, command.actor_id, stored)
        return stored


class RemoveProjectAttachmentUseCase(_AttachmentUseCase):
    """Takes a file away. Anyone on the team may: a file is the mission's."""

    async def execute(self, command: RemoveAttachmentCommand) -> ProjectAttachment:
        attachment = await self._attachments.get(command.attachment_id)
        if attachment is None:
            raise EntityNotFoundError("The file cannot be found.")

        # The line goes first, the bytes after. An object nobody points at is
        # invisible; a line pointing at no object is a broken screen.
        await self._attachments.remove(command.attachment_id)
        await self._store.delete(attachment.storage_key)
        await self._trace(AuditAction.ATTACHMENT_REMOVE, command.actor_id, attachment)
        return attachment


class ListProjectAttachmentsUseCase:
    """A mission's files, each signed and each knowing what shows it."""

    def __init__(
        self,
        attachments: ProjectAttachmentRepository,
        updates: ProjectUpdateRepository,
        users: UserRepository,
    ) -> None:
        self._attachments = attachments
        self._updates = updates
        self._users = users

    async def execute(self, project_id: int) -> list[SignedAttachment]:
        held = await self._attachments.list_for_project(project_id)
        if not held:
            return []

        users = {u.id: u for u in await self._users.list_all(True)}
        shown = await self._shown_in_updates(project_id)
        return [
            SignedAttachment(
                attachment=attachment,
                uploader=users[attachment.uploaded_by],
                used_in_updates=shown.get(attachment.id, 0),
            )
            for attachment in held
            if attachment.uploaded_by in users
        ]

    async def _shown_in_updates(self, project_id: int) -> dict[int | None, int]:
        """How many updates of the mission display each file."""
        counts: dict[int | None, int] = {}
        for update in await self._updates.list_for_project(project_id):
            for attachment_id in referenced_ids(update.body):
                counts[attachment_id] = counts.get(attachment_id, 0) + 1
        return counts


class DownloadProjectAttachmentUseCase:
    """A file and its bytes."""

    def __init__(
        self, attachments: ProjectAttachmentRepository, store: AttachmentStore
    ) -> None:
        self._attachments = attachments
        self._store = store

    async def execute(self, attachment_id: int) -> tuple[ProjectAttachment, bytes]:
        attachment = await self._attachments.get(attachment_id)
        if attachment is None:
            raise EntityNotFoundError("The file cannot be found.")
        return attachment, await self._store.get(attachment.storage_key)
