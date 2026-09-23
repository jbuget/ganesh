"""Reading one month of the register back, against a real PostgreSQL database."""

from datetime import date, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.audit_logs.domain.entities.audit_log import (
    AuditAction,
    AuditLog,
    AuditLogFilter,
)
from src.modules.audit_logs.infrastructure.database.repositories.audit_log_repository_impl import (
    SqlAuditLogRepository,
)
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)
from src.shared.utils import clock

pytestmark = pytest.mark.db

SEPTEMBER = date(2026, 9, 1)


async def a_teammate(session: AsyncSession, oid: str) -> int:
    person = await SqlUserRepository(session).add(
        User(
            id=None,
            entra_oid=oid,
            email=f"{oid}@waat.fr",
            display_name=oid,
            role=Role.TEAMMATE,
        )
    )
    assert person.id is not None
    return person.id


def a_declaration(target_user_id: int, day: date, at: datetime) -> AuditLog:
    return AuditLog(
        action=AuditAction.ENTRY_SET,
        actor_id=target_user_id,
        target_user_id=target_user_id,
        day=day,
        at=clock.as_instant(at),
    )


@pytest.mark.asyncio
async def test_a_month_is_read_most_recent_first_and_counted_whole(
    db_session: AsyncSession,
) -> None:
    repository = SqlAuditLogRepository(db_session)
    person = await a_teammate(db_session, "oid-month")
    for rank in (1, 3, 2):
        await repository.add(
            a_declaration(person, date(2026, 9, rank), datetime(2026, 9, rank, 9, 0))
        )

    page = await repository.list_for_user_month(person, SEPTEMBER, limit=2, offset=0)

    assert [log.day for log in page] == [date(2026, 9, 3), date(2026, 9, 2)]
    assert await repository.count_for_user_month(person, SEPTEMBER) == 3


@pytest.mark.asyncio
async def test_a_month_leaves_out_the_months_around_it(
    db_session: AsyncSession,
) -> None:
    repository = SqlAuditLogRepository(db_session)
    person = await a_teammate(db_session, "oid-edges")
    for day in (date(2026, 8, 31), date(2026, 9, 30), date(2026, 10, 1)):
        await repository.add(
            a_declaration(person, day, datetime(day.year, day.month, day.day, 9, 0))
        )

    page = await repository.list_for_user_month(person, SEPTEMBER, limit=50, offset=0)

    assert [log.day for log in page] == [date(2026, 9, 30)]
    assert await repository.count_for_user_month(person, SEPTEMBER) == 1


@pytest.mark.asyncio
async def test_a_month_carries_what_holds_for_the_whole_of_it(
    db_session: AsyncSession,
) -> None:
    """A validation is dated by the month it locks, and belongs to its log."""
    repository = SqlAuditLogRepository(db_session)
    person = await a_teammate(db_session, "oid-validated")
    await repository.add(
        AuditLog(
            action=AuditAction.MONTH_VALIDATE,
            actor_id=person,
            target_user_id=person,
            day=SEPTEMBER,
            at=clock.as_instant(datetime(2026, 10, 1, 9, 0)),
        )
    )

    page = await repository.list_for_user_month(person, SEPTEMBER, limit=50, offset=0)

    assert [log.action for log in page] == [AuditAction.MONTH_VALIDATE]


@pytest.mark.asyncio
async def test_a_month_keeps_to_whose_it_is(db_session: AsyncSession) -> None:
    repository = SqlAuditLogRepository(db_session)
    mine = await a_teammate(db_session, "oid-mine")
    theirs = await a_teammate(db_session, "oid-theirs")
    await repository.add(
        a_declaration(mine, date(2026, 9, 3), datetime(2026, 9, 3, 9, 0))
    )
    await repository.add(
        a_declaration(theirs, date(2026, 9, 3), datetime(2026, 9, 3, 10, 0))
    )

    page = await repository.list_for_user_month(mine, SEPTEMBER, limit=50, offset=0)

    assert [log.target_user_id for log in page] == [mine]


@pytest.mark.asyncio
async def test_the_whole_register_is_narrowed_by_what_was_asked(
    db_session: AsyncSession,
) -> None:
    """The criteria answer together, and the tally counts the same window.

    A count taken over the whole register beside a narrowed page would promise
    pages that are not there, and « Voir plus » would never stop offering.
    """
    repository = SqlAuditLogRepository(db_session)
    mine = await a_teammate(db_session, "oid-narrowed-mine")
    theirs = await a_teammate(db_session, "oid-narrowed-theirs")
    for actor, action, at in (
        (mine, AuditAction.PROJECT_DELETE, datetime(2026, 9, 10, 9, 0)),
        (mine, AuditAction.PROJECT_CREATE, datetime(2026, 9, 10, 9, 0)),
        (theirs, AuditAction.PROJECT_DELETE, datetime(2026, 9, 10, 9, 0)),
        (mine, AuditAction.PROJECT_DELETE, datetime(2026, 8, 1, 9, 0)),
    ):
        await repository.add(
            AuditLog(action=action, actor_id=actor, at=clock.as_instant(at))
        )

    kept = AuditLogFilter(
        since=clock.opens(date(2026, 9, 1)),
        until=clock.closes(date(2026, 9, 30)),
        actions=[AuditAction.PROJECT_DELETE],
        actor_id=mine,
    )
    page = await repository.list_all(limit=50, offset=0, kept=kept)

    assert [log.action for log in page] == [AuditAction.PROJECT_DELETE]
    assert await repository.count_all(kept) == 1


@pytest.mark.asyncio
async def test_a_period_given_in_days_holds_both_of_its_ends(
    db_session: AsyncSession,
) -> None:
    """« du 3 au 3 » reads the 3rd, at either end of the day."""
    repository = SqlAuditLogRepository(db_session)
    person = await a_teammate(db_session, "oid-both-ends")
    for at in (
        datetime(2026, 9, 3, 0, 5),
        datetime(2026, 9, 3, 23, 55),
        datetime(2026, 9, 4, 0, 5),
    ):
        await repository.add(
            AuditLog(
                action=AuditAction.PROJECT_CREATE,
                actor_id=person,
                at=clock.as_instant(at),
            )
        )

    kept = AuditLogFilter(
        since=clock.opens(date(2026, 9, 3)),
        until=clock.closes(date(2026, 9, 3)),
        actor_id=person,
    )

    assert await repository.count_all(kept) == 2


@pytest.mark.asyncio
async def test_asking_for_no_gesture_at_all_answers_nothing(
    db_session: AsyncSession,
) -> None:
    """A reader who cleared every box is not handed the register back."""
    repository = SqlAuditLogRepository(db_session)
    person = await a_teammate(db_session, "oid-no-gesture")
    await repository.add(
        AuditLog(action=AuditAction.PROJECT_CREATE, actor_id=person, at=clock.now())
    )

    kept = AuditLogFilter(actions=[])

    assert await repository.list_all(limit=50, offset=0, kept=kept) == []
    assert await repository.count_all(kept) == 0
