"""The routes that read one's inbox and settle what has been seen."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.notifications.application.use_cases.list_my_notifications import (
    ListMyNotificationsUseCase,
)
from src.modules.notifications.application.use_cases.set_notifications_read_state import (
    SetNotificationsReadStateUseCase,
)
from src.modules.notifications.domain.entities.notification import (
    Notification,
    NotificationKind,
)
from src.modules.notifications.presentation.dependencies import (
    get_list_my_notifications_use_case,
    get_set_notifications_read_state_use_case,
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
SITE = Project(
    id=42,
    label="Refonte du site",
    kind=ProjectKind.PROJECT,
    status=ProjectStatus.DEVELOPMENT,
)
NOTIFICATIONS = f"{get_settings().api_prefix}/notifications"


@dataclass
class Screen:
    """A signed-in teammate and the inbox their calls land on."""

    client: AsyncClient
    inbox: InMemoryNotificationRepository

    async def read(self, query: str = ""):
        return await self.client.get(f"{NOTIFICATIONS}{query}")

    async def settle(self, **payload):
        return await self.client.post(f"{NOTIFICATIONS}/read-state", json=payload)


def sign_in(lines: list[Notification] | None = None) -> Screen:
    inbox = InMemoryNotificationRepository()
    for line in lines or []:
        inbox.notifications.append(line)
        line.id = len(inbox.notifications)
    inbox._next_id = len(inbox.notifications) + 1
    users = InMemoryUserRepository([ALICE, BOB])
    projects = InMemoryProjectRepository([SITE])

    app.dependency_overrides[get_current_user] = lambda: ALICE
    app.dependency_overrides[get_list_my_notifications_use_case] = (
        lambda: ListMyNotificationsUseCase(
            notifications=inbox, users=users, projects=projects
        )
    )
    app.dependency_overrides[get_set_notifications_read_state_use_case] = (
        lambda: SetNotificationsReadStateUseCase(inbox)
    )
    return Screen(
        client=AsyncClient(transport=ASGITransport(app=app), base_url="http://test"),
        inbox=inbox,
    )


def assigned(
    recipient_id: int = 1, at: datetime = MONDAY, actor_id: int = 2
) -> Notification:
    return Notification(
        recipient_id=recipient_id,
        kind=NotificationKind.PROJECT_ASSIGNED,
        actor_id=actor_id,
        at=at,
        project_id=42,
        payload={"role": "referent"},
    )


@pytest.fixture(autouse=True)
def _forget_the_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


async def test_an_empty_inbox_answers_a_page_with_nothing_in_it() -> None:
    response = await sign_in().read()

    assert response.status_code == 200
    assert response.json() == {"total": 0, "unread_count": 0, "entries": []}


async def test_a_line_names_who_acted_and_on_what() -> None:
    response = await sign_in([assigned()]).read()

    [entry] = response.json()["entries"]
    assert entry["kind"] == "project.assigned"
    assert entry["actor"] == {
        "id": 2,
        "display_name": "G. Belhadj",
        "initials": "GB",
    }
    assert entry["project"] == {"id": 42, "label": "Refonte du site"}
    assert entry["read_at"] is None
    assert entry["count"] == 1
    assert entry["payload"] == {"role": "referent"}


async def test_one_only_ever_reads_ones_own_inbox() -> None:
    """A line addressed to a colleague is not in mine."""
    response = await sign_in([assigned(recipient_id=2, actor_id=1)]).read()

    assert response.json()["entries"] == []


async def test_asking_for_what_is_waiting_leaves_the_bell_alone() -> None:
    seen = assigned(at=TUESDAY)
    seen.mark_read(at=TUESDAY)
    screen = sign_in([assigned(), seen])

    response = await screen.read("?status=unread")

    body = response.json()
    assert len(body["entries"]) == 1
    assert body["unread_count"] == 1


async def test_marking_one_line_seen_hands_back_what_is_left() -> None:
    screen = sign_in([assigned(), assigned(at=TUESDAY)])

    response = await screen.settle(ids=[1], read=True)

    assert response.status_code == 200
    assert response.json() == {"updated": 1, "unread_count": 1}


async def test_marking_everything_seen() -> None:
    screen = sign_in([assigned(), assigned(at=TUESDAY)])

    response = await screen.settle(read=True)

    assert response.json() == {"updated": 2, "unread_count": 0}


async def test_putting_a_line_back_in_waiting() -> None:
    seen = assigned()
    seen.mark_read(at=TUESDAY)
    screen = sign_in([seen])

    response = await screen.settle(ids=[1], read=False)

    assert response.json() == {"updated": 1, "unread_count": 1}


async def test_knowing_a_colleagues_line_id_is_not_enough_to_settle_it() -> None:
    screen = sign_in([assigned(recipient_id=2, actor_id=1)])

    response = await screen.settle(ids=[1], read=True)

    assert response.json() == {"updated": 0, "unread_count": 0}
    assert screen.inbox.notifications[0].is_read is False


async def test_a_page_larger_than_the_cap_is_refused() -> None:
    assert (await sign_in().read("?limit=500")).status_code == 422


async def test_a_filter_that_does_not_exist_is_refused() -> None:
    assert (await sign_in().read("?status=maybe")).status_code == 422
