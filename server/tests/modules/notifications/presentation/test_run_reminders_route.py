"""The route by which a manager sends the round by hand."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.notifications.application.use_cases.send_due_reminders import (
    SendDueRemindersUseCase,
)
from src.modules.notifications.domain.entities.letter import Letter
from src.modules.notifications.domain.entities.notification import (
    Notification,
    NotificationKind,
)
from src.modules.notifications.domain.repositories.mailer import (
    Mailer,
    MailerUnavailableError,
)
from src.modules.notifications.presentation.dependencies import (
    get_send_due_reminders_use_case,
)
from src.modules.users.domain.entities.reminder_cadence import ReminderCadence
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryNotificationRepository,
    InMemoryUserRepository,
)

URL = f"{get_settings().api_prefix}/notifications/reminders/run"


def a_manager() -> User:
    return User(
        id=9,
        entra_oid="oid-9",
        email="g.belhadj@waat.fr",
        display_name="G. Belhadj",
        role=Role.MANAGER,
        reminder_cadence=ReminderCadence.NEVER,
    )


def a_teammate() -> User:
    return User(
        id=2,
        entra_oid="oid-2",
        email="l.chen@waat.fr",
        display_name="L. Chen",
        role=Role.TEAMMATE,
        reminder_cadence=ReminderCadence.DAILY,
    )


class CollectingMailer(Mailer):
    def __init__(self) -> None:
        self.sent: list[Letter] = []

    async def send(self, letter: Letter) -> None:
        self.sent.append(letter)


class UnusableMailer(Mailer):
    async def send(self, letter: Letter) -> None:
        raise MailerUnavailableError("the mail server refused our credentials")


def stand_up(signed_in_as: str, mailer: Mailer) -> None:
    """A fresh team each time.

    Built per test rather than shared: a round moves `reminder_sent_at` on the
    objects it writes to, and a module-level User would carry one test's stamp
    into the next.
    """
    manager, teammate = a_manager(), a_teammate()
    signed_in = manager if signed_in_as == "manager" else teammate
    users = InMemoryUserRepository([manager, teammate])
    inbox = InMemoryNotificationRepository()
    waiting = Notification(
        recipient_id=2,
        kind=NotificationKind.UPDATE_MENTION,
        actor_id=9,
        at=datetime.now(UTC),
    )
    inbox.notifications.append(waiting)
    waiting.id = 1

    app.dependency_overrides[get_current_user] = lambda: signed_in
    app.dependency_overrides[get_send_due_reminders_use_case] = (
        lambda: SendDueRemindersUseCase(
            users=users,
            notifications=inbox,
            mailer=mailer,
            audit_logs=InMemoryAuditLogRepository(),
            web_url="https://ganesh.waat.tools",
        )
    )


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()


async def test_a_manager_sends_the_round(client: AsyncClient) -> None:
    post = CollectingMailer()
    stand_up("manager", post)

    response = await client.post(URL, json={"cadence": "DAILY"})

    assert response.status_code == 200
    assert response.json() == {"sent": 1}
    assert [letter.to for letter in post.sent] == ["l.chen@waat.fr"]


async def test_a_teammate_is_turned_away(client: AsyncClient) -> None:
    # It writes to the whole team at once.
    post = CollectingMailer()
    stand_up("teammate", post)

    response = await client.post(URL, json={"cadence": "DAILY"})

    assert response.status_code == 403
    assert post.sent == []


async def test_nowhere_to_post_answers_503_rather_than_400(
    client: AsyncClient,
) -> None:
    # The answer worth having when one is testing the configuration: it is not
    # the caller's request that is wrong.
    stand_up("manager", UnusableMailer())

    response = await client.post(URL, json={"cadence": "DAILY"})

    assert response.status_code == 503
    assert "mail server" in response.json()["detail"]


async def test_a_cadence_the_domain_does_not_hold_is_refused(
    client: AsyncClient,
) -> None:
    stand_up("manager", CollectingMailer())

    response = await client.post(URL, json={"cadence": "HOURLY"})

    assert response.status_code == 422


async def test_the_round_must_be_named(client: AsyncClient) -> None:
    # « chaque jour » and « chaque semaine » are two sets of readers, and a
    # button that sent both would write to whoever asked for one a week.
    stand_up("manager", CollectingMailer())

    response = await client.post(URL, json={})

    assert response.status_code == 422


async def test_asking_for_the_other_cadence_writes_to_nobody(
    client: AsyncClient,
) -> None:
    post = CollectingMailer()
    stand_up("manager", post)

    response = await client.post(URL, json={"cadence": "WEEKLY"})

    assert response.status_code == 200
    assert response.json() == {"sent": 0}
    assert post.sent == []
