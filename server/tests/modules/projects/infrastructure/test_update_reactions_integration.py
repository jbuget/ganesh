"""The signs left under an update, against a real database.

The in-memory double walks a list and dedups by hand; the database leans on a
three-column key and `ON CONFLICT DO NOTHING`. That is the whole idempotency of
the gesture, so it is worth covering where it actually lives.
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.projects.domain.entities.update_reaction import (
    Reaction,
    UpdateReaction,
)
from src.modules.projects.infrastructure.database.repositories.project_repository_impl import (
    SqlProjectRepository,
)
from src.modules.projects.infrastructure.database.repositories.project_update_repository_impl import (
    SqlProjectUpdateRepository,
)
from src.modules.projects.infrastructure.database.repositories.update_reaction_repository_impl import (
    SqlUpdateReactionRepository,
)
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)

pytestmark = pytest.mark.db

WHEN = datetime(2026, 9, 17, 10, 0, tzinfo=UTC)


async def a_thread(db_session: AsyncSession) -> tuple[int, int, int]:
    """One update, one on another mission, one author. Returns their ids."""
    people = SqlUserRepository(db_session)
    author = await people.add(
        User(
            id=None,
            entra_oid="oid-signe",
            email="signe@waat.fr",
            display_name="L. Chen",
            role=Role.TEAMMATE,
        )
    )
    projects = SqlProjectRepository(db_session)
    updates = SqlProjectUpdateRepository(db_session)
    written = []
    for label in ["Portail", "Extranet"]:
        mission = await projects.add(
            Project(
                id=None,
                label=label,
                kind=ProjectKind.PROJECT,
                status=ProjectStatus.SCOPING,
            )
        )
        assert mission.id is not None and author.id is not None
        written.append(
            await updates.add(
                ProjectUpdate(
                    id=None,
                    project_id=mission.id,
                    author_id=author.id,
                    body=f"Point sur {label}.",
                    published_at=WHEN,
                )
            )
        )
    assert written[0].id and written[1].id and author.id
    return written[0].id, written[1].id, author.id


async def test_the_same_sign_left_twice_counts_once(db_session: AsyncSession) -> None:
    update_id, _, who = await a_thread(db_session)
    reactions = SqlUpdateReactionRepository(db_session)
    sign = UpdateReaction(update_id, who, Reaction.THUMBS_UP, WHEN)

    await reactions.add(sign)
    await reactions.add(sign)

    assert len((await reactions.list_for_updates([update_id]))[update_id]) == 1


async def test_one_person_may_leave_several_different_signs(
    db_session: AsyncSession,
) -> None:
    update_id, _, who = await a_thread(db_session)
    reactions = SqlUpdateReactionRepository(db_session)

    for sign in (Reaction.EYES, Reaction.ROCKET):
        await reactions.add(UpdateReaction(update_id, who, sign, WHEN))

    left = (await reactions.list_for_updates([update_id]))[update_id]
    assert {one.reaction for one in left} == {Reaction.EYES, Reaction.ROCKET}


async def test_only_the_updates_asked_for_come_back(db_session: AsyncSession) -> None:
    update_id, elsewhere, who = await a_thread(db_session)
    reactions = SqlUpdateReactionRepository(db_session)
    await reactions.add(UpdateReaction(update_id, who, Reaction.HEART, WHEN))

    assert list(await reactions.list_for_updates([update_id])) == [update_id]
    assert await reactions.list_for_updates([elsewhere]) == {}


async def test_an_empty_thread_asks_nothing(db_session: AsyncSession) -> None:
    """A mission with no message must not send `IN ()` to the database."""
    assert await SqlUpdateReactionRepository(db_session).list_for_updates([]) == {}


async def test_a_sign_is_taken_back(db_session: AsyncSession) -> None:
    update_id, _, who = await a_thread(db_session)
    reactions = SqlUpdateReactionRepository(db_session)
    await reactions.add(UpdateReaction(update_id, who, Reaction.HEART, WHEN))

    await reactions.remove(update_id, who, Reaction.HEART)

    assert await reactions.list_for_updates([update_id]) == {}


async def test_taking_back_a_sign_never_left_changes_nothing(
    db_session: AsyncSession,
) -> None:
    update_id, _, who = await a_thread(db_session)
    reactions = SqlUpdateReactionRepository(db_session)
    await reactions.add(UpdateReaction(update_id, who, Reaction.HEART, WHEN))

    await reactions.remove(update_id, who, Reaction.EYES)

    assert len((await reactions.list_for_updates([update_id]))[update_id]) == 1


async def test_signs_come_back_in_the_order_people_left_them(
    db_session: AsyncSession,
) -> None:
    update_id, _, first = await a_thread(db_session)
    later = await SqlUserRepository(db_session).add(
        User(
            id=None,
            entra_oid="oid-second",
            email="n.garo.ext@waat.fr",
            display_name="N. Garo",
            role=Role.TEAMMATE,
        )
    )
    assert later.id is not None
    reactions = SqlUpdateReactionRepository(db_session)
    await reactions.add(
        UpdateReaction(
            update_id,
            later.id,
            Reaction.THUMBS_UP,
            datetime(2026, 9, 18, 9, 0, tzinfo=UTC),
        )
    )
    await reactions.add(UpdateReaction(update_id, first, Reaction.THUMBS_UP, WHEN))

    left = (await reactions.list_for_updates([update_id]))[update_id]
    assert [one.user_id for one in left] == [first, later.id]
