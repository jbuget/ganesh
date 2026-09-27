"""The replies written under an update, against a real database.

The in-memory double reads a mission through the updates it is handed; the
database reads it through a join, and dedups the authors of a conversation
with a walk the double does differently. Both are worth covering where they
actually live.
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.projects.domain.entities.comment_reaction import CommentReaction
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.projects.domain.entities.update_comment import UpdateComment
from src.modules.projects.domain.entities.update_reaction import Reaction
from src.modules.projects.infrastructure.database.repositories.comment_reaction_repository_impl import (
    SqlCommentReactionRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_repository_impl import (
    SqlProjectRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_update_repository_impl import (
    SqlProjectUpdateRepository,
)
from src.modules.projects.infrastructure.database.repositories.update_comment_repository_impl import (
    SqlUpdateCommentRepository,
)
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)

pytestmark = pytest.mark.db

WHEN = datetime(2026, 9, 27, 10, 0, tzinfo=UTC)


async def a_conversation(db_session: AsyncSession) -> tuple[int, int, int, int]:
    """Two missions, an update on each, two people. Returns their ids."""
    people = SqlUserRepository(db_session)
    written = []
    for who in ["l.chen", "n.garo"]:
        written.append(
            await people.add(
                User(
                    id=None,
                    entra_oid=f"oid-{who}",
                    email=f"{who}@waat.fr",
                    display_name=who,
                    role=Role.TEAMMATE,
                )
            )
        )
    alice, nino = written

    projects = SqlProjectRepository(db_session)
    updates = SqlProjectUpdateRepository(db_session)
    posted = []
    for label in ["Portail", "Extranet"]:
        mission = await projects.add(
            Project(
                id=None,
                label=label,
                kind=ProjectKind.PROJECT,
                status=ProjectStatus.SCOPING,
            )
        )
        assert mission.id is not None and alice.id is not None
        posted.append(
            (
                mission.id,
                await updates.add(
                    ProjectUpdate(
                        id=None,
                        project_id=mission.id,
                        author_id=alice.id,
                        body="Ou en est le POC ?",
                        published_at=WHEN,
                    )
                ),
            )
        )
    (portail, here), (_, elsewhere) = posted
    assert here.id is not None and elsewhere.id is not None
    assert alice.id is not None and nino.id is not None
    return portail, here.id, elsewhere.id, nino.id


async def test_a_conversation_comes_back_oldest_first(
    db_session: AsyncSession,
) -> None:
    _, update_id, _, nino = await a_conversation(db_session)
    comments = SqlUpdateCommentRepository(db_session)
    for minute, body in [(30, "Second."), (10, "Premier.")]:
        await comments.add(
            UpdateComment(
                id=None,
                update_id=update_id,
                author_id=nino,
                body=body,
                published_at=WHEN + timedelta(minutes=minute),
            )
        )

    found = await comments.list_for_updates([update_id])

    assert [one.body for one in found[update_id]] == ["Premier.", "Second."]


async def test_a_reply_is_read_under_the_mission_of_the_update_it_answers(
    db_session: AsyncSession,
) -> None:
    portail, here, elsewhere, nino = await a_conversation(db_session)
    comments = SqlUpdateCommentRepository(db_session)
    for update_id, body in [(here, "Sur le portail."), (elsewhere, "Ailleurs.")]:
        await comments.add(
            UpdateComment(
                id=None,
                update_id=update_id,
                author_id=nino,
                body=body,
                published_at=WHEN,
            )
        )

    found = await comments.list_for_project(portail)

    assert [one.body for one in found] == ["Sur le portail."]


async def test_the_authors_of_a_conversation_are_named_once_each(
    db_session: AsyncSession,
) -> None:
    _, update_id, _, nino = await a_conversation(db_session)
    comments = SqlUpdateCommentRepository(db_session)
    for minute in (10, 20):
        await comments.add(
            UpdateComment(
                id=None,
                update_id=update_id,
                author_id=nino,
                body="Encore moi.",
                published_at=WHEN + timedelta(minutes=minute),
            )
        )

    assert await comments.authors_for_update(update_id) == [nino]


async def test_a_withdrawn_reply_keeps_its_place_and_loses_its_words(
    db_session: AsyncSession,
) -> None:
    _, update_id, _, nino = await a_conversation(db_session)
    comments = SqlUpdateCommentRepository(db_session)
    written = await comments.add(
        UpdateComment(
            id=None,
            update_id=update_id,
            author_id=nino,
            body="Fini hier soir.",
            published_at=WHEN,
        )
    )
    written.remove(by=nino, at=WHEN)

    await comments.update(written)

    assert written.id is not None
    read_back = await comments.get(written.id)
    assert read_back is not None
    assert read_back.is_deleted
    assert read_back.body == ""


async def test_leaving_the_same_sign_twice_under_a_reply_changes_nothing(
    db_session: AsyncSession,
) -> None:
    """The three-column key is where the idempotency actually lives."""
    _, update_id, _, nino = await a_conversation(db_session)
    comments = SqlUpdateCommentRepository(db_session)
    written = await comments.add(
        UpdateComment(
            id=None,
            update_id=update_id,
            author_id=nino,
            body="Fini hier soir.",
            published_at=WHEN,
        )
    )
    assert written.id is not None
    reactions = SqlCommentReactionRepository(db_session)
    sign = CommentReaction(
        comment_id=written.id, user_id=nino, reaction=Reaction.THUMBS_UP, at=WHEN
    )

    await reactions.add(sign)
    await reactions.add(sign)

    found = await reactions.list_for_comments([written.id])
    assert len(found[written.id]) == 1


async def test_a_sign_is_taken_back_from_under_a_reply(
    db_session: AsyncSession,
) -> None:
    _, update_id, _, nino = await a_conversation(db_session)
    comments = SqlUpdateCommentRepository(db_session)
    written = await comments.add(
        UpdateComment(
            id=None,
            update_id=update_id,
            author_id=nino,
            body="Fini hier soir.",
            published_at=WHEN,
        )
    )
    assert written.id is not None
    reactions = SqlCommentReactionRepository(db_session)
    await reactions.add(
        CommentReaction(
            comment_id=written.id, user_id=nino, reaction=Reaction.HEART, at=WHEN
        )
    )

    await reactions.remove(written.id, nino, Reaction.HEART)

    assert await reactions.list_for_comments([written.id]) == {}
