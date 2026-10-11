"""Looking after the vocabulary of tags.

Anybody opens a tag by typing it on a mission; what keeps the vocabulary from
drifting is that a manager can rename it, recolour it, and fold a duplicate
into the tag it should have been. Those three move every mission carrying the
tag at once, and each writes one line per mission — a single summary line
would live in no mission's journal.
"""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.application.dtos.tag_dto import (
    MergeTagsCommand,
    RecolorTagCommand,
    RenameTagCommand,
)
from src.modules.projects.domain.entities.tag import Tag, TagUsage, tag_key
from src.modules.projects.domain.repositories.project_tag_repository import (
    ProjectTagRepository,
)
from src.modules.projects.domain.repositories.tag_repository import TagRepository
from src.modules.projects.domain.services.tag_search import search_tags
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    ConflictError,
    EntityNotFoundError,
    ValidationError,
)


class ListTagsUseCase:
    """The tags somebody may pick from, closest to what they typed first.

    Typing nothing gives every tag in use, the most carried first: that is the
    list a filter is drawn from.
    """

    def __init__(self, tags: TagRepository) -> None:
        self._tags = tags

    async def execute(self, typed: str | None) -> list[TagUsage]:
        return search_tags(typed or "", await self._tags.list_in_use())


class _VocabularyGesture:
    """What the gestures on the vocabulary share: who makes them, the tag they
    bear on, and the trace left on each mission carrying it."""

    def __init__(
        self,
        users: UserRepository,
        tags: TagRepository,
        links: ProjectTagRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._users = users
        self._tags = tags
        self._links = links
        self._audit_logs = audit_logs

    async def _load_tag(self, actor_id: int, tag_id: int) -> Tag:
        if await self._users.get_by_id(actor_id) is None:
            raise EntityNotFoundError("The user cannot be found.")
        tag = await self._tags.get_by_id(tag_id)
        if tag is None:
            raise EntityNotFoundError("The tag cannot be found.")
        return tag

    async def _trace(
        self,
        action: AuditAction,
        actor_id: int,
        project_id: int,
        tag: Tag,
        old_value: str,
        new_value: str,
    ) -> None:
        await self._audit_logs.add(
            AuditLog(
                action=action,
                actor_id=actor_id,
                project_id=project_id,
                old_value=old_value,
                new_value=new_value,
                payload={"tag_id": tag.stored_id, "tag": tag.name},
            )
        )


class RenameTagUseCase(_VocabularyGesture):
    """Renames a tag for every mission that carries it."""

    async def execute(self, command: RenameTagCommand) -> Tag:
        tag = await self._load_tag(command.actor_id, command.tag_id)
        previous = tag.name
        if command.name.strip() == previous:
            return tag

        # Another tag already saying the same thing is what merging is for:
        # renaming into it would leave two tags with one key.
        taken_by = await self._tags.get_by_key(tag_key(command.name))
        if taken_by is not None and taken_by.id != tag.id:
            raise ConflictError(
                f"A tag already says « {taken_by.name} »: fold this one into it."
            )

        tag.rename(command.name)
        await self._tags.update(tag)
        for project_id in await self._links.project_ids_for(tag.stored_id):
            await self._trace(
                AuditAction.TAG_RENAME,
                command.actor_id,
                project_id,
                tag,
                previous,
                tag.name,
            )
        return tag


class RecolorTagUseCase(_VocabularyGesture):
    """Gives a tag another colour of the palette, for every mission."""

    async def execute(self, command: RecolorTagCommand) -> Tag:
        tag = await self._load_tag(command.actor_id, command.tag_id)
        previous = tag.color
        if command.color is previous:
            return tag

        tag.recolor(command.color)
        await self._tags.update(tag)
        for project_id in await self._links.project_ids_for(tag.stored_id):
            await self._trace(
                AuditAction.TAG_RECOLOR,
                command.actor_id,
                project_id,
                tag,
                previous.value,
                tag.color.value,
            )
        return tag


class MergeTagsUseCase(_VocabularyGesture):
    """Folds a tag into another one that says the same thing.

    Every mission carrying the first carries the second afterwards, and the
    first is gone. A mission carrying both is left with the one kept, so the
    merge never makes a mission cross the bound on tags: it swaps one for one,
    or sheds one.
    """

    async def execute(self, command: MergeTagsCommand) -> Tag:
        if command.source_id == command.target_id:
            raise ValidationError("A tag cannot be folded into itself.")
        source = await self._load_tag(command.actor_id, command.source_id)
        target = await self._load_tag(command.actor_id, command.target_id)

        for project_id in await self._links.project_ids_for(source.stored_id):
            await self._links.attach(project_id, target.stored_id)
            await self._links.detach(project_id, source.stored_id)
            await self._trace(
                AuditAction.TAG_MERGE,
                command.actor_id,
                project_id,
                target,
                source.name,
                target.name,
            )
        await self._tags.delete(source.stored_id)
        return target
