"""Reading one's own inbox."""

from datetime import datetime

import pytest

from src.modules.notifications.application.use_cases.list_my_notifications import (
    ListMyNotificationsUseCase,
)
from src.modules.notifications.domain.entities.notification import (
    Notification,
    NotificationKind,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryNotificationRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
)

MONDAY = datetime(2026, 1, 12, 9, 0)
TUESDAY = datetime(2026, 1, 13, 9, 0)

ALICE = User(
    id=1,
    entra_oid="oid-1",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)
BOB = User(
    id=2,
    entra_oid="oid-2",
    email="g.belhadj@waat.fr",
    display_name="G. Belhadj",
    role=Role.MANAGER,
)


@pytest.fixture
def inbox():
    notifications = InMemoryNotificationRepository()
    users = InMemoryUserRepository([ALICE, BOB])
    projects = InMemoryProjectRepository(
        [
            Project(
                id=42,
                label="Refonte du site",
                kind=ProjectKind.PROJECT,
                status=ProjectStatus.DEVELOPMENT,
            )
        ]
    )
    return (
        ListMyNotificationsUseCase(
            notifications=notifications, users=users, projects=projects
        ),
        notifications,
    )


def assigned(recipient_id: int, at: datetime) -> Notification:
    return Notification(
        recipient_id=recipient_id,
        kind=NotificationKind.PROJECT_ASSIGNED,
        actor_id=2,
        at=at,
        project_id=42,
    )


@pytest.mark.asyncio
async def test_an_empty_inbox_reads_empty(inbox) -> None:
    use_case, _ = inbox

    feed = await use_case.execute(recipient_id=1, unread_only=False, limit=20, offset=0)

    assert feed.entries == []
    assert feed.total == 0
    assert feed.unread_count == 0


@pytest.mark.asyncio
async def test_a_notification_comes_back_with_who_acted_and_on_what(inbox) -> None:
    use_case, notifications = inbox
    await notifications.add(assigned(1, MONDAY))

    feed = await use_case.execute(recipient_id=1, unread_only=False, limit=20, offset=0)

    assert feed.entries[0].actor == BOB
    assert feed.entries[0].project is not None
    assert feed.entries[0].project.label == "Refonte du site"


@pytest.mark.asyncio
async def test_one_only_ever_reads_ones_own_inbox(inbox) -> None:
    use_case, notifications = inbox
    await notifications.add(assigned(1, MONDAY))

    feed = await use_case.execute(recipient_id=2, unread_only=False, limit=20, offset=0)

    assert feed.entries == []


@pytest.mark.asyncio
async def test_the_unread_count_travels_with_the_page(inbox) -> None:
    use_case, notifications = inbox
    await notifications.add(assigned(1, MONDAY))
    seen = await notifications.add(assigned(1, TUESDAY))
    seen.mark_read(at=TUESDAY)

    feed = await use_case.execute(recipient_id=1, unread_only=False, limit=20, offset=0)

    assert feed.total == 2
    assert feed.unread_count == 1


@pytest.mark.asyncio
async def test_asking_for_the_unread_ones_leaves_the_count_whole(inbox) -> None:
    """The filter narrows the page, never the figure the bell shows."""
    use_case, notifications = inbox
    await notifications.add(assigned(1, MONDAY))
    seen = await notifications.add(assigned(1, TUESDAY))
    seen.mark_read(at=TUESDAY)

    feed = await use_case.execute(recipient_id=1, unread_only=True, limit=20, offset=0)

    assert len(feed.entries) == 1
    assert feed.total == 1
    assert feed.unread_count == 1


@pytest.mark.asyncio
async def test_a_line_naming_a_mission_that_is_gone_still_reads(inbox) -> None:
    use_case, notifications = inbox
    await notifications.add(
        Notification(
            recipient_id=1,
            kind=NotificationKind.PROJECT_DELETED,
            actor_id=2,
            at=MONDAY,
            payload={"project_label": "Ancien chantier"},
        )
    )

    feed = await use_case.execute(recipient_id=1, unread_only=False, limit=20, offset=0)

    assert feed.entries[0].project is None
    assert feed.entries[0].notification.payload == {"project_label": "Ancien chantier"}
