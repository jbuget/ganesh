"""How a gesture lands: a new line, or one more on the line already waiting."""

from datetime import date, datetime

import pytest

from src.modules.notifications.domain.entities.notification import (
    Notification,
    NotificationKind,
)
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from tests.helpers.in_memory_repositories import InMemoryNotificationRepository

MONDAY = datetime(2026, 1, 12, 9, 0)
TUESDAY = datetime(2026, 1, 13, 9, 0)
JANUARY = date(2026, 1, 1)


def an_edit(at: datetime, month: date = JANUARY) -> Notification:
    return Notification(
        recipient_id=1,
        kind=NotificationKind.TIMESHEET_EDITED,
        actor_id=2,
        at=at,
        day=month,
    )


@pytest.fixture
def delivery() -> tuple[NotificationDelivery, InMemoryNotificationRepository]:
    repository = InMemoryNotificationRepository()
    return NotificationDelivery(repository), repository


@pytest.mark.asyncio
async def test_a_first_gesture_opens_a_line(delivery) -> None:
    service, repository = delivery

    await service.deliver([an_edit(MONDAY)])

    assert len(repository.notifications) == 1
    assert repository.notifications[0].count == 1


@pytest.mark.asyncio
async def test_the_same_gesture_again_folds_into_the_line_waiting(delivery) -> None:
    """Twenty-two half-days posted on a month ring once."""
    service, repository = delivery
    await service.deliver([an_edit(MONDAY)])

    await service.deliver([an_edit(TUESDAY)])

    assert len(repository.notifications) == 1
    assert repository.notifications[0].count == 2
    assert repository.notifications[0].at == TUESDAY


@pytest.mark.asyncio
async def test_two_months_edited_stay_two_lines(delivery) -> None:
    service, repository = delivery
    await service.deliver([an_edit(MONDAY)])

    await service.deliver([an_edit(TUESDAY, month=date(2026, 2, 1))])

    assert len(repository.notifications) == 2


@pytest.mark.asyncio
async def test_a_line_already_seen_is_not_folded_into(delivery) -> None:
    """One has seen what was done yesterday, not what is being done now."""
    service, repository = delivery
    await service.deliver([an_edit(MONDAY)])
    repository.notifications[0].mark_read(at=MONDAY)

    await service.deliver([an_edit(TUESDAY)])

    assert len(repository.notifications) == 2


@pytest.mark.asyncio
async def test_a_gesture_made_on_purpose_never_folds(delivery) -> None:
    """Two updates posted on a mission are two things to read."""
    service, repository = delivery
    posted = Notification(
        recipient_id=1,
        kind=NotificationKind.PROJECT_UPDATE_POSTED,
        actor_id=2,
        at=MONDAY,
        project_id=42,
    )

    await service.deliver([posted])
    await service.deliver([Notification(**{**vars(posted), "id": None, "at": TUESDAY})])

    assert len(repository.notifications) == 2
