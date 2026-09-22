"""Declared rhythms, against a real PostgreSQL database."""

from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.calendar.domain.entities.week_pattern import FULL_TIME, WeekPattern
from src.modules.users.domain.entities.rhythm import Rhythm
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.infrastructure.database.repositories.rhythm_repository_impl import (
    SqlRhythmRepository,
)
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)

pytestmark = pytest.mark.db

MARCH = date(2026, 3, 1)
SEPTEMBER = date(2026, 9, 1)
WEDNESDAY_IN_JUNE = date(2026, 6, 17)

FOUR_FIFTHS = WeekPattern(wednesday=0.0)
HALF_TIME = WeekPattern(wednesday=0.0, thursday=0.0, friday=0.0)


async def a_teammate(session: AsyncSession, oid: str) -> int:
    user = await SqlUserRepository(session).add(
        User(
            id=None,
            entra_oid=oid,
            email=f"{oid}@waat.fr",
            display_name="Rythme",
            role=Role.TEAMMATE,
        )
    )
    assert user.id is not None
    return user.id


async def test_a_declared_rhythm_is_read_back_as_declared(
    db_session: AsyncSession,
) -> None:
    repository = SqlRhythmRepository(db_session)
    user_id = await a_teammate(db_session, "oid-declared")

    await repository.declare(
        Rhythm(id=None, user_id=user_id, pattern=FOUR_FIFTHS, effective_from=MARCH)
    )

    history = await repository.history_of(user_id)
    assert history.pattern_on(WEDNESDAY_IN_JUNE) == FOUR_FIFTHS


async def test_declaring_twice_on_one_day_corrects_rather_than_piles_up(
    db_session: AsyncSession,
) -> None:
    repository = SqlRhythmRepository(db_session)
    user_id = await a_teammate(db_session, "oid-corrected")

    await repository.declare(
        Rhythm(id=None, user_id=user_id, pattern=FOUR_FIFTHS, effective_from=MARCH)
    )
    await repository.declare(
        Rhythm(id=None, user_id=user_id, pattern=HALF_TIME, effective_from=MARCH)
    )

    history = await repository.history_of(user_id)
    assert history.pattern_on(WEDNESDAY_IN_JUNE) == HALF_TIME


async def test_each_rhythm_holds_until_the_next_one_opens(
    db_session: AsyncSession,
) -> None:
    repository = SqlRhythmRepository(db_session)
    user_id = await a_teammate(db_session, "oid-succession")

    await repository.declare(
        Rhythm(id=None, user_id=user_id, pattern=FOUR_FIFTHS, effective_from=MARCH)
    )
    await repository.declare(
        Rhythm(id=None, user_id=user_id, pattern=HALF_TIME, effective_from=SEPTEMBER)
    )

    history = await repository.history_of(user_id)
    assert history.pattern_on(WEDNESDAY_IN_JUNE) == FOUR_FIFTHS
    assert history.pattern_on(date(2026, 9, 16)) == HALF_TIME


async def test_everyone_asked_for_comes_back_declared_or_not(
    db_session: AsyncSession,
) -> None:
    # Whoever declared nothing is full time, and the caller should not have to
    # tell a missing key from an empty history to know it.
    repository = SqlRhythmRepository(db_session)
    declared = await a_teammate(db_session, "oid-has-one")
    silent = await a_teammate(db_session, "oid-has-none")

    await repository.declare(
        Rhythm(id=None, user_id=declared, pattern=FOUR_FIFTHS, effective_from=MARCH)
    )

    histories = await repository.histories_of([declared, silent])

    assert histories[declared].pattern_on(WEDNESDAY_IN_JUNE) == FOUR_FIFTHS
    assert histories[silent].pattern_on(WEDNESDAY_IN_JUNE) == FULL_TIME
