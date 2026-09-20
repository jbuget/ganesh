"""Marking lines seen, or putting them back in waiting."""

from datetime import datetime

import pytest

from src.modules.notifications.application.dtos.notification_dtos import (
    ReadStateCommand,
)
from src.modules.notifications.application.use_cases.set_notifications_read_state import (
    SetNotificationsReadStateUseCase,
)
from src.modules.notifications.domain.entities.notification import (
    Notification,
    NotificationKind,
)
from tests.helpers.in_memory_repositories import InMemoryNotificationRepository

MONDAY = datetime(2026, 1, 12, 9, 0)
TUESDAY = datetime(2026, 1, 13, 9, 0)


def a_line(recipient_id: int) -> Notification:
    return Notification(
        recipient_id=recipient_id,
        kind=NotificationKind.PROJECT_ASSIGNED,
        actor_id=99,
        at=MONDAY,
        project_id=42,
    )


@pytest.fixture
def repository() -> InMemoryNotificationRepository:
    return InMemoryNotificationRepository()


@pytest.mark.asyncio
async def test_marking_one_line_seen(repository) -> None:
    line = await repository.add(a_line(1))
    use_case = SetNotificationsReadStateUseCase(repository)

    touched = await use_case.execute(
        ReadStateCommand(recipient_id=1, ids=[line.id], read=True), now=TUESDAY
    )

    assert touched.updated == 1
    assert line.read_at == TUESDAY


@pytest.mark.asyncio
async def test_marking_everything_seen_at_once(repository) -> None:
    await repository.add(a_line(1))
    await repository.add(a_line(1))
    use_case = SetNotificationsReadStateUseCase(repository)

    touched = await use_case.execute(
        ReadStateCommand(recipient_id=1, ids=None, read=True), now=TUESDAY
    )

    assert touched.updated == 2
    assert all(line.is_read for line in repository.notifications)


@pytest.mark.asyncio
async def test_putting_a_line_back_in_waiting(repository) -> None:
    line = await repository.add(a_line(1))
    line.mark_read(at=MONDAY)
    use_case = SetNotificationsReadStateUseCase(repository)

    await use_case.execute(
        ReadStateCommand(recipient_id=1, ids=[line.id], read=False), now=TUESDAY
    )

    assert line.is_read is False


@pytest.mark.asyncio
async def test_knowing_the_id_of_someone_elses_line_is_not_enough(repository) -> None:
    """Whose inbox it is, is checked where it is read — never by the caller."""
    someone_elses = await repository.add(a_line(2))
    use_case = SetNotificationsReadStateUseCase(repository)

    touched = await use_case.execute(
        ReadStateCommand(recipient_id=1, ids=[someone_elses.id], read=True),
        now=TUESDAY,
    )

    assert touched.updated == 0
    assert someone_elses.is_read is False


@pytest.mark.asyncio
async def test_marking_seen_what_was_already_seen_changes_nothing(repository) -> None:
    line = await repository.add(a_line(1))
    line.mark_read(at=MONDAY)
    use_case = SetNotificationsReadStateUseCase(repository)

    touched = await use_case.execute(
        ReadStateCommand(recipient_id=1, ids=None, read=True), now=TUESDAY
    )

    assert touched.updated == 0
    assert line.read_at == MONDAY


@pytest.mark.asyncio
async def test_what_is_left_waiting_comes_back_with_the_answer(repository) -> None:
    """The bell settles without asking again."""
    line = await repository.add(a_line(1))
    await repository.add(a_line(1))
    use_case = SetNotificationsReadStateUseCase(repository)

    outcome = await use_case.execute(
        ReadStateCommand(recipient_id=1, ids=[line.id], read=True), now=TUESDAY
    )

    assert outcome.unread_count == 1
