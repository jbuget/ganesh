"""Answering an update, under it."""

from datetime import datetime

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.projects.application.dtos.update_dto import (
    EditCommentCommand,
    PostCommentCommand,
    ReactToCommentCommand,
    RemoveCommentCommand,
)
from src.modules.projects.application.use_cases.project_updates import (
    ListProjectUpdatesUseCase,
)
from src.modules.projects.application.use_cases.update_comments import (
    EditCommentUseCase,
    PostCommentUseCase,
    ReactToCommentUseCase,
    RemoveCommentUseCase,
    WithdrawCommentReactionUseCase,
)
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.projects.domain.entities.update_reaction import Reaction
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryCommentReactionRepository,
    InMemoryNotificationRepository,
    InMemoryProjectUpdateRepository,
    InMemoryUpdateCommentRepository,
    InMemoryUpdateReactionRepository,
    InMemoryUserRepository,
)

pytestmark = pytest.mark.asyncio

ALICE = User(
    id=1,
    entra_oid="oid-1",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)
NINO = User(
    id=2,
    entra_oid="oid-2",
    email="n.garo.ext@waat.fr",
    display_name="N. Garo",
    role=Role.TEAMMATE,
)
SAM = User(
    id=3,
    entra_oid="oid-3",
    email="s.roux@waat.fr",
    display_name="S. Roux",
    role=Role.TEAMMATE,
)
WHEN = datetime(2026, 9, 27, 10, 0)
LATER = datetime(2026, 9, 27, 11, 0)


class Thread:
    """A mission's thread with one update on it, and every gesture on a reply."""

    def __init__(self) -> None:
        self.updates = InMemoryProjectUpdateRepository()
        self.comments = InMemoryUpdateCommentRepository(self.updates)
        self.reactions = InMemoryCommentReactionRepository()
        self.audit = InMemoryAuditLogRepository()
        self.inbox = InMemoryNotificationRepository()
        users = InMemoryUserRepository([ALICE, NINO, SAM])
        shared = {
            "updates": self.updates,
            "comments": self.comments,
            "audit_logs": self.audit,
        }
        self.post = PostCommentUseCase(
            **shared, notifications=NotificationDelivery(self.inbox)
        )
        self.edit = EditCommentUseCase(**shared)
        self.withdraw = RemoveCommentUseCase(**shared)
        self.react = ReactToCommentUseCase(
            comments=self.comments, reactions=self.reactions
        )
        self.unreact = WithdrawCommentReactionUseCase(reactions=self.reactions)
        self.read = ListProjectUpdatesUseCase(
            updates=self.updates,
            users=users,
            reactions=InMemoryUpdateReactionRepository(),
            comments=self.comments,
            comment_reactions=self.reactions,
        )

    async def with_an_update(self, author: int = ALICE.id or 1) -> int:
        update = await self.updates.add(
            ProjectUpdate(
                id=None,
                project_id=10,
                author_id=author,
                body="Ou en est le POC ?",
                published_at=WHEN,
            )
        )
        assert update.id is not None
        return update.id

    async def answer(self, update_id: int, by: int, body: str = "Fini hier soir."):
        return await self.post.execute(
            PostCommentCommand(actor_id=by, update_id=update_id, body=body),
            now=LATER,
        )


async def test_a_reply_hangs_under_the_update_it_answers() -> None:
    thread = Thread()
    update_id = await thread.with_an_update()

    comment = await thread.answer(update_id, by=2)

    assert comment.update_id == update_id
    assert comment.author_id == 2
    assert comment.body == "Fini hier soir."


async def test_answering_an_update_nobody_posted_is_refused() -> None:
    with pytest.raises(EntityNotFoundError):
        await Thread().answer(404, by=2)


async def test_the_thread_carries_its_conversation() -> None:
    thread = Thread()
    update_id = await thread.with_an_update()
    await thread.answer(update_id, by=2, body="Fini hier soir.")
    await thread.answer(update_id, by=3, body="Super.")

    [signed] = await thread.read.execute(10)

    assert [one.comment.body for one in signed.comments] == [
        "Fini hier soir.",
        "Super.",
    ]
    assert [one.author.label for one in signed.comments] == ["N. Garo", "S. Roux"]


async def test_a_conversation_is_read_forward() -> None:
    """The thread runs backwards; the conversation under a line does not."""
    thread = Thread()
    update_id = await thread.with_an_update()
    first = await thread.answer(update_id, by=2, body="Premier.")
    second = await thread.answer(update_id, by=3, body="Second.")

    [signed] = await thread.read.execute(10)

    assert [one.comment.id for one in signed.comments] == [first.id, second.id]


async def test_the_author_corrects_their_own_reply() -> None:
    thread = Thread()
    comment = await thread.answer(await thread.with_an_update(), by=2)

    assert comment.id is not None
    await thread.edit.execute(
        EditCommentCommand(actor_id=2, comment_id=comment.id, body="Fini ce matin."),
        now=LATER,
    )

    assert comment.body == "Fini ce matin."


async def test_nobody_corrects_the_reply_of_another() -> None:
    thread = Thread()
    comment = await thread.answer(await thread.with_an_update(), by=2)

    assert comment.id is not None
    with pytest.raises(ForbiddenActionError):
        await thread.edit.execute(
            EditCommentCommand(actor_id=3, comment_id=comment.id, body="Autre chose")
        )


async def test_a_withdrawn_reply_keeps_its_place() -> None:
    thread = Thread()
    update_id = await thread.with_an_update()
    comment = await thread.answer(update_id, by=2)

    assert comment.id is not None
    await thread.withdraw.execute(
        RemoveCommentCommand(actor_id=2, comment_id=comment.id), now=LATER
    )

    [signed] = await thread.read.execute(10)
    assert len(signed.comments) == 1
    assert signed.comments[0].comment.is_deleted
    assert signed.comments[0].comment.body == ""


async def test_every_movement_on_a_reply_is_traced() -> None:
    """The register reads a project; a reply is words said on it."""
    thread = Thread()
    update_id = await thread.with_an_update()
    comment = await thread.answer(update_id, by=2)
    assert comment.id is not None
    await thread.edit.execute(
        EditCommentCommand(actor_id=2, comment_id=comment.id, body="Fini ce matin.")
    )
    await thread.withdraw.execute(
        RemoveCommentCommand(actor_id=2, comment_id=comment.id)
    )

    assert [line.action for line in thread.audit.logs] == [
        AuditAction.COMMENT_POST,
        AuditAction.COMMENT_EDIT,
        AuditAction.COMMENT_REMOVE,
    ]
    # Against the mission the update belongs to, read off the update itself.
    assert {line.project_id for line in thread.audit.logs} == {10}
    assert thread.audit.logs[0].payload == {
        "update_id": update_id,
        "comment_id": comment.id,
    }


async def test_the_author_of_the_update_hears_the_answer() -> None:
    thread = Thread()
    update_id = await thread.with_an_update(author=1)

    await thread.answer(update_id, by=2)

    told = [(one.recipient_id, one.kind) for one in thread.inbox.notifications]
    assert told == [(1, NotificationKind.UPDATE_REPLIED)]


async def test_whoever_already_answered_hears_the_next_reply() -> None:
    thread = Thread()
    update_id = await thread.with_an_update(author=1)
    await thread.answer(update_id, by=2)
    thread.inbox.notifications.clear()

    await thread.answer(update_id, by=3, body="Super.")

    told = {one.recipient_id for one in thread.inbox.notifications}
    assert told == {1, 2}


async def test_nobody_hears_their_own_reply() -> None:
    thread = Thread()
    update_id = await thread.with_an_update(author=1)

    await thread.answer(update_id, by=1, body="Je precise.")

    assert thread.inbox.notifications == []


async def test_the_mission_is_not_told_of_every_ok_written_underneath() -> None:
    """Being in the conversation is what puts one here, not being on the
    mission: that line went out when the update did."""
    thread = Thread()
    update_id = await thread.with_an_update(author=1)

    await thread.answer(update_id, by=2)

    assert {one.recipient_id for one in thread.inbox.notifications} == {1}


async def test_being_named_in_a_reply_is_heard() -> None:
    thread = Thread()
    update_id = await thread.with_an_update(author=1)

    await thread.answer(
        update_id, by=2, body="@[S. Roux](mention://user/3) peux-tu relire ?"
    )

    told = {one.recipient_id: one.kind for one in thread.inbox.notifications}
    assert told[3] is NotificationKind.UPDATE_MENTION


async def test_being_named_is_louder_than_being_in_the_conversation() -> None:
    thread = Thread()
    update_id = await thread.with_an_update(author=1)

    await thread.answer(
        update_id, by=2, body="@[L. Chen](mention://user/1) c'est fait."
    )

    told = [(one.recipient_id, one.kind) for one in thread.inbox.notifications]
    assert told == [(1, NotificationKind.UPDATE_MENTION)]


async def test_a_sign_is_left_under_a_reply() -> None:
    thread = Thread()
    comment = await thread.answer(await thread.with_an_update(), by=2)

    assert comment.id is not None
    await thread.react.execute(
        ReactToCommentCommand(
            actor_id=1, comment_id=comment.id, reaction=Reaction.THUMBS_UP
        )
    )

    [signed] = await thread.read.execute(10)
    [bar] = signed.comments[0].reactions
    assert bar.reaction is Reaction.THUMBS_UP
    assert [who.label for who in bar.people] == ["L. Chen"]


async def test_leaving_the_same_sign_twice_changes_nothing() -> None:
    thread = Thread()
    comment = await thread.answer(await thread.with_an_update(), by=2)
    assert comment.id is not None
    sign = ReactToCommentCommand(
        actor_id=1, comment_id=comment.id, reaction=Reaction.HEART
    )

    await thread.react.execute(sign)
    await thread.react.execute(sign)

    assert len(thread.reactions.reactions) == 1


async def test_one_takes_back_one_s_own_sign() -> None:
    thread = Thread()
    comment = await thread.answer(await thread.with_an_update(), by=2)
    assert comment.id is not None
    sign = ReactToCommentCommand(
        actor_id=1, comment_id=comment.id, reaction=Reaction.HEART
    )
    await thread.react.execute(sign)

    await thread.unreact.execute(sign)

    assert thread.reactions.reactions == []


async def test_a_sign_under_a_reply_nobody_wrote_is_refused() -> None:
    with pytest.raises(EntityNotFoundError):
        await Thread().react.execute(
            ReactToCommentCommand(
                actor_id=1, comment_id=404, reaction=Reaction.THUMBS_UP
            )
        )
