"""The notification repository, against a real PostgreSQL database."""

from datetime import date, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.notifications.domain.entities.notification import (
    Notification,
    NotificationKind,
)
from src.modules.notifications.infrastructure.database.repositories.notification_repository_impl import (
    SqlNotificationRepository,
)
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)

pytestmark = pytest.mark.db

MONDAY = datetime(2026, 1, 12, 9, 0)
TUESDAY = datetime(2026, 1, 13, 9, 0)
JANUARY = date(2026, 1, 1)


async def seed(session: AsyncSession) -> tuple[int, int]:
    """Two teammates, and their identifiers."""
    users = SqlUserRepository(session)
    alice = await users.add(
        User(
            id=None,
            entra_oid="oid-notif-1",
            email="l.chen@waat.fr",
            display_name="L. Chen",
            role=Role.TEAMMATE,
        )
    )
    bob = await users.add(
        User(
            id=None,
            entra_oid="oid-notif-2",
            email="g.belhadj@waat.fr",
            display_name="G. Belhadj",
            role=Role.MANAGER,
        )
    )
    assert alice.id is not None and bob.id is not None
    return alice.id, bob.id


def an_edit(recipient_id: int, actor_id: int, at: datetime) -> Notification:
    return Notification(
        recipient_id=recipient_id,
        kind=NotificationKind.TIMESHEET_EDITED,
        actor_id=actor_id,
        at=at,
        day=JANUARY,
    )


async def test_a_notification_is_persisted_and_read_back(
    db_session: AsyncSession,
) -> None:
    alice, bob = await seed(db_session)
    repository = SqlNotificationRepository(db_session)

    await repository.add(an_edit(alice, bob, MONDAY))

    [line] = await repository.list_for(alice, unread_only=False, limit=20, offset=0)
    assert line.kind is NotificationKind.TIMESHEET_EDITED
    assert line.actor_id == bob
    assert line.day == JANUARY
    assert line.count == 1
    assert line.is_read is False


async def test_the_kind_is_stored_under_the_name_of_its_member(
    db_session: AsyncSession,
) -> None:
    """`native_enum=False`: the database holds the member's name."""
    alice, bob = await seed(db_session)
    await SqlNotificationRepository(db_session).add(an_edit(alice, bob, MONDAY))

    stored = await db_session.execute(
        text("SELECT kind FROM notifications WHERE recipient_id = :id"),
        {"id": alice},
    )
    assert stored.scalar_one() == "TIMESHEET_EDITED"


async def test_an_inbox_holds_nobody_elses_lines(db_session: AsyncSession) -> None:
    alice, bob = await seed(db_session)
    repository = SqlNotificationRepository(db_session)
    await repository.add(an_edit(alice, bob, MONDAY))

    assert await repository.count_for(bob, unread_only=False) == 0


async def test_the_twin_of_a_waiting_line_is_found(db_session: AsyncSession) -> None:
    alice, bob = await seed(db_session)
    repository = SqlNotificationRepository(db_session)
    await repository.add(an_edit(alice, bob, MONDAY))

    twin = await repository.find_open_twin(
        recipient_id=alice,
        kind=NotificationKind.TIMESHEET_EDITED,
        actor_id=bob,
        day=JANUARY,
    )

    assert twin is not None


async def test_a_line_already_seen_is_no_twin(db_session: AsyncSession) -> None:
    alice, bob = await seed(db_session)
    repository = SqlNotificationRepository(db_session)
    await repository.add(an_edit(alice, bob, MONDAY))
    await repository.set_read_state(alice, ids=None, read=True, at=TUESDAY)

    twin = await repository.find_open_twin(
        recipient_id=alice,
        kind=NotificationKind.TIMESHEET_EDITED,
        actor_id=bob,
        day=JANUARY,
    )

    assert twin is None


async def test_absorbing_writes_the_count_and_the_moment_back(
    db_session: AsyncSession,
) -> None:
    alice, bob = await seed(db_session)
    repository = SqlNotificationRepository(db_session)
    line = await repository.add(an_edit(alice, bob, MONDAY))

    line.absorb(at=TUESDAY)
    await repository.save(line)

    [read_back] = await repository.list_for(
        alice, unread_only=False, limit=20, offset=0
    )
    assert read_back.count == 2
    assert read_back.at == TUESDAY


async def test_marking_seen_only_touches_ones_own_lines(
    db_session: AsyncSession,
) -> None:
    alice, bob = await seed(db_session)
    repository = SqlNotificationRepository(db_session)
    someone_elses = await repository.add(an_edit(bob, alice, MONDAY))

    touched = await repository.set_read_state(
        alice, ids=[someone_elses.id], read=True, at=TUESDAY
    )

    assert touched == 0
    assert await repository.count_for(bob, unread_only=True) == 1


async def test_marking_everything_seen_leaves_nothing_waiting(
    db_session: AsyncSession,
) -> None:
    alice, bob = await seed(db_session)
    repository = SqlNotificationRepository(db_session)
    await repository.add(an_edit(alice, bob, MONDAY))
    await repository.add(
        Notification(
            recipient_id=alice,
            kind=NotificationKind.PROJECT_ASSIGNED,
            actor_id=bob,
            at=TUESDAY,
        )
    )

    touched = await repository.set_read_state(alice, ids=None, read=True, at=TUESDAY)

    assert touched == 2
    assert await repository.count_for(alice, unread_only=True) == 0
    assert await repository.count_for(alice, unread_only=False) == 2


async def test_putting_a_line_back_in_waiting(db_session: AsyncSession) -> None:
    alice, bob = await seed(db_session)
    repository = SqlNotificationRepository(db_session)
    line = await repository.add(an_edit(alice, bob, MONDAY))
    await repository.set_read_state(alice, ids=None, read=True, at=TUESDAY)

    touched = await repository.set_read_state(
        alice, ids=[line.id], read=False, at=TUESDAY
    )

    assert touched == 1
    assert await repository.count_for(alice, unread_only=True) == 1


async def test_the_page_reads_most_recent_first(db_session: AsyncSession) -> None:
    alice, bob = await seed(db_session)
    repository = SqlNotificationRepository(db_session)
    await repository.add(an_edit(alice, bob, MONDAY))
    await repository.add(
        Notification(
            recipient_id=alice,
            kind=NotificationKind.PROJECT_ASSIGNED,
            actor_id=bob,
            at=TUESDAY,
        )
    )

    lines = await repository.list_for(alice, unread_only=False, limit=20, offset=0)

    assert [line.kind for line in lines] == [
        NotificationKind.PROJECT_ASSIGNED,
        NotificationKind.TIMESHEET_EDITED,
    ]


async def test_a_line_survives_the_account_that_acted(db_session: AsyncSession) -> None:
    """The actor is released, not cascaded: what one was told stays told."""
    alice, bob = await seed(db_session)
    repository = SqlNotificationRepository(db_session)
    await repository.add(an_edit(alice, bob, MONDAY))
    await db_session.execute(text("DELETE FROM users WHERE id = :id"), {"id": bob})

    [line] = await repository.list_for(alice, unread_only=False, limit=20, offset=0)
    assert line.actor_id == 0
