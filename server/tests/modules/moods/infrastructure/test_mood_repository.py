"""The mood repository, against a real PostgreSQL database."""

from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.moods.domain.entities.mood import Mood, MoodLevel
from src.modules.moods.infrastructure.database.repositories.mood_repository_impl import (
    SqlMoodRepository,
)
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)

pytestmark = pytest.mark.db

MONDAY = date(2026, 9, 14)
TUESDAY = date(2026, 9, 15)


async def seed(session: AsyncSession) -> tuple[int, int]:
    """Two teammates, and their identifiers."""
    users = SqlUserRepository(session)
    alice = await users.add(
        User(
            id=None,
            entra_oid="oid-mood-1",
            email="l.chen@waat.fr",
            display_name="L. Chen",
            role=Role.TEAMMATE,
        )
    )
    bob = await users.add(
        User(
            id=None,
            entra_oid="oid-mood-2",
            email="g.belhadj@waat.fr",
            display_name="G. Belhadj",
            role=Role.TEAMMATE,
        )
    )
    assert alice.id is not None and bob.id is not None
    return alice.id, bob.id


async def test_a_mood_is_persisted_and_read_back(db_session: AsyncSession) -> None:
    alice, _ = await seed(db_session)
    moods = SqlMoodRepository(db_session)

    await moods.upsert(Mood(id=None, user_id=alice, day=TUESDAY, level=MoodLevel.GOOD))

    saved = await moods.get(alice, TUESDAY)
    assert saved is not None
    assert saved.level is MoodLevel.GOOD


async def test_posting_twice_keeps_a_single_row(db_session: AsyncSession) -> None:
    alice, _ = await seed(db_session)
    moods = SqlMoodRepository(db_session)

    await moods.upsert(Mood(id=None, user_id=alice, day=TUESDAY, level=MoodLevel.BAD))
    await moods.upsert(
        Mood(id=None, user_id=alice, day=TUESDAY, level=MoodLevel.EXCELLENT)
    )

    rows = await moods.list_between(TUESDAY, TUESDAY)
    assert len(rows) == 1
    assert rows[0].level is MoodLevel.EXCELLENT


async def test_the_window_holds_the_whole_team(db_session: AsyncSession) -> None:
    alice, bob = await seed(db_session)
    moods = SqlMoodRepository(db_session)

    await moods.upsert(Mood(id=None, user_id=alice, day=TUESDAY, level=MoodLevel.HARD))
    await moods.upsert(Mood(id=None, user_id=bob, day=MONDAY, level=MoodLevel.NEUTRAL))

    assert len(await moods.list_between(MONDAY, TUESDAY)) == 2
    assert len(await moods.list_between(TUESDAY, TUESDAY)) == 1


async def test_ones_own_window_leaves_out_the_colleagues(
    db_session: AsyncSession,
) -> None:
    alice, bob = await seed(db_session)
    moods = SqlMoodRepository(db_session)

    await moods.upsert(Mood(id=None, user_id=alice, day=TUESDAY, level=MoodLevel.HARD))
    await moods.upsert(Mood(id=None, user_id=bob, day=TUESDAY, level=MoodLevel.GOOD))

    mine = await moods.list_for_user_between(alice, MONDAY, TUESDAY)
    assert [mood.level for mood in mine] == [MoodLevel.HARD]


async def test_the_level_is_stored_under_the_name_of_its_member(
    db_session: AsyncSession,
) -> None:
    """`native_enum=False` stores the name: any hand-written SQL reads it."""
    alice, _ = await seed(db_session)
    await SqlMoodRepository(db_session).upsert(
        Mood(id=None, user_id=alice, day=TUESDAY, level=MoodLevel.EXCELLENT)
    )

    stored = await db_session.execute(
        text("SELECT level FROM moods WHERE user_id = :user_id"),
        {"user_id": alice},
    )
    assert stored.scalar_one() == "EXCELLENT"
