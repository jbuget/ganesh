"""The lock that makes the number of processes stop mattering."""

from datetime import UTC, date, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.scheduler.claim import claim

pytestmark = pytest.mark.db

DAY = date(2026, 9, 23)
AT = datetime(2026, 9, 23, 8, 30, tzinfo=UTC)


async def test_the_first_to_ask_takes_the_run(db_session: AsyncSession) -> None:
    assert await claim(db_session, "reminder:daily", DAY, AT) is True


async def test_the_second_finds_it_already_taken(db_session: AsyncSession) -> None:
    # Four workers waking at once send one letter, not four.
    await claim(db_session, "reminder:daily", DAY, AT)

    assert await claim(db_session, "reminder:daily", DAY, AT) is False


async def test_a_restart_does_not_do_the_day_again(db_session: AsyncSession) -> None:
    # Idempotence comes with the lock: a deploy at 9 h does not re-send the
    # round of 8 h 30.
    await claim(db_session, "reminder:daily", DAY, AT)

    assert (
        await claim(
            db_session,
            "reminder:daily",
            DAY,
            datetime(2026, 9, 23, 9, 0, tzinfo=UTC),
        )
        is False
    )


async def test_two_rounds_on_one_day_are_two_claims(db_session: AsyncSession) -> None:
    await claim(db_session, "reminder:daily", DAY, AT)

    assert await claim(db_session, "reminder:weekly", DAY, AT) is True


async def test_the_next_day_is_a_run_of_its_own(db_session: AsyncSession) -> None:
    await claim(db_session, "reminder:daily", DAY, AT)

    assert await claim(db_session, "reminder:daily", date(2026, 9, 24), AT) is True
