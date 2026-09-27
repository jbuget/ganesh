"""Answering an update in the thread: write, correct, withdraw, sign."""

from datetime import datetime

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.notifications.domain.services.fan_out import notify
from src.modules.projects.application.dtos.update_dto import (
    EditCommentCommand,
    PostCommentCommand,
    ReactToCommentCommand,
    RemoveCommentCommand,
)
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.projects.domain.entities.update_comment import UpdateComment
from src.modules.projects.domain.repositories.comment_reaction_repository import (
    CommentReactionRepository,
)
from src.modules.projects.domain.repositories.project_update_repository import (
    ProjectUpdateRepository,
)
from src.modules.projects.domain.repositories.update_comment_repository import (
    UpdateCommentRepository,
)
from src.modules.projects.domain.services.mentions import mentioned_ids
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from src.shared.utils import clock


class _CommentUseCase:
    """What the three writes on a reply share: loading it, and tracing it.

    A comment is traced in the register like the update it answers: it is
    words said on the mission, and the « Journal » tab reads back everything
    carrying the project. The mission is read off the update the reply hangs
    from rather than passed in again — one argument fewer is one chance fewer
    of tracing a gesture against the wrong project.
    """

    def __init__(
        self,
        updates: ProjectUpdateRepository,
        comments: UpdateCommentRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._updates = updates
        self._comments = comments
        self._audit_logs = audit_logs

    async def _load_update(self, update_id: int) -> ProjectUpdate:
        update = await self._updates.get(update_id)
        if update is None:
            raise EntityNotFoundError("Unknown update.")
        return update

    async def _load(self, comment_id: int) -> tuple[UpdateComment, ProjectUpdate]:
        comment = await self._comments.get(comment_id)
        if comment is None:
            raise EntityNotFoundError("Unknown comment.")
        return comment, await self._load_update(comment.update_id)

    async def _trace(
        self,
        action: AuditAction,
        actor_id: int,
        comment: UpdateComment,
        update: ProjectUpdate,
    ) -> None:
        await self._audit_logs.add(
            AuditLog(
                action=action,
                actor_id=actor_id,
                project_id=update.project_id,
                payload={"update_id": update.id, "comment_id": comment.id},
            )
        )


class PostCommentUseCase(_CommentUseCase):
    """Answers an update, under it."""

    def __init__(
        self,
        updates: ProjectUpdateRepository,
        comments: UpdateCommentRepository,
        audit_logs: AuditLogRepository,
        notifications: NotificationDelivery,
    ) -> None:
        super().__init__(updates=updates, comments=comments, audit_logs=audit_logs)
        self._notifications = notifications

    async def execute(
        self, command: PostCommentCommand, now: datetime | None = None
    ) -> UpdateComment:
        update = await self._load_update(command.update_id)
        # Who was in the conversation before this reply: the next one hears
        # about itself, this one does not.
        already = await self._comments.authors_for_update(command.update_id)

        comment = await self._comments.add(
            update.reply(command.actor_id, command.body, at=now or clock.now())
        )
        assert comment.id is not None
        await self._trace(AuditAction.COMMENT_POST, command.actor_id, comment, update)
        await self._tell_the_conversation(comment, update, already)
        return comment

    async def _tell_the_conversation(
        self,
        comment: UpdateComment,
        update: ProjectUpdate,
        already: list[int],
    ) -> None:
        """Who hears a reply, and under what heading.

        The conversation rather than the mission: whoever wrote the update and
        whoever has already answered under it. Everybody else on the mission
        was told when the update went up and does not need a line for every
        « ok » written beneath it.

        Being named is louder than being in the conversation: someone who is
        both gets the one line that says they were spoken to, and not two.
        """
        named = mentioned_ids(comment.body)
        payload = {"update_id": update.id, "comment_id": comment.id}

        await self._notifications.deliver(
            notify(
                NotificationKind.UPDATE_MENTION,
                actor_id=comment.author_id,
                recipients=named,
                at=comment.published_at,
                project_id=update.project_id,
                payload=payload,
            )
        )
        await self._notifications.deliver(
            notify(
                NotificationKind.UPDATE_REPLIED,
                actor_id=comment.author_id,
                recipients=[
                    who for who in [update.author_id, *already] if who not in named
                ],
                at=comment.published_at,
                project_id=update.project_id,
                payload=payload,
            )
        )


class EditCommentUseCase(_CommentUseCase):
    """Corrects a reply. Author only, as the entity makes sure."""

    async def execute(
        self, command: EditCommentCommand, now: datetime | None = None
    ) -> UpdateComment:
        comment, update = await self._load(command.comment_id)
        comment.rewrite(command.body, by=command.actor_id, at=now or clock.now())
        await self._comments.update(comment)
        await self._trace(AuditAction.COMMENT_EDIT, command.actor_id, comment, update)
        return comment


class RemoveCommentUseCase(_CommentUseCase):
    """Withdraws a reply. It keeps its place in the conversation."""

    async def execute(
        self, command: RemoveCommentCommand, now: datetime | None = None
    ) -> None:
        comment, update = await self._load(command.comment_id)
        comment.remove(by=command.actor_id, at=now or clock.now())
        await self._comments.update(comment)
        await self._trace(AuditAction.COMMENT_REMOVE, command.actor_id, comment, update)


class ReactToCommentUseCase:
    """Answers a reply without writing another one.

    Nothing is traced and nobody is told, as under an update: a sign decides
    nothing and is left by the dozen.
    """

    def __init__(
        self,
        comments: UpdateCommentRepository,
        reactions: CommentReactionRepository,
    ) -> None:
        self._comments = comments
        self._reactions = reactions

    async def execute(
        self, command: ReactToCommentCommand, now: datetime | None = None
    ) -> None:
        comment = await self._comments.get(command.comment_id)
        if comment is None:
            raise EntityNotFoundError("Unknown comment.")
        await self._reactions.add(
            comment.react(command.actor_id, command.reaction, at=now or clock.now())
        )


class WithdrawCommentReactionUseCase:
    """Takes a sign back from under a reply, one's own and nobody else's."""

    def __init__(self, reactions: CommentReactionRepository) -> None:
        self._reactions = reactions

    async def execute(self, command: ReactToCommentCommand) -> None:
        await self._reactions.remove(
            comment_id=command.comment_id,
            user_id=command.actor_id,
            reaction=command.reaction,
        )
