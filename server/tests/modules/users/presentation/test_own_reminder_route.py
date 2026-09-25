"""The route by which everyone says how often they are written to."""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.users.application.use_cases.choose_own_reminder_cadence import (
    ChooseOwnReminderCadenceUseCase,
)
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.presentation.dependencies import (
    get_choose_own_reminder_cadence_use_case,
)
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryUserRepository,
)

TEAMMATE = User(
    id=2,
    entra_oid="oid-2",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)

URL = f"{get_settings().api_prefix}/users/me/reminder-cadence"


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    users = InMemoryUserRepository([TEAMMATE])
    app.dependency_overrides[get_current_user] = lambda: TEAMMATE
    app.dependency_overrides[get_choose_own_reminder_cadence_use_case] = (
        lambda: ChooseOwnReminderCadenceUseCase(
            users=users, audit_logs=InMemoryAuditLogRepository()
        )
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()


async def test_a_teammate_asks_for_the_weekly_letter(client: AsyncClient) -> None:
    response = await client.put(URL, json={"cadence": "WEEKLY"})

    assert response.status_code == 200
    assert response.json()["reminder_cadence"] == "WEEKLY"


async def test_a_teammate_asks_for_no_letter_at_all(client: AsyncClient) -> None:
    response = await client.put(URL, json={"cadence": "NEVER"})

    assert response.status_code == 200
    assert response.json()["reminder_cadence"] == "NEVER"


async def test_a_cadence_the_domain_does_not_hold_is_refused(
    client: AsyncClient,
) -> None:
    response = await client.put(URL, json={"cadence": "HOURLY"})

    assert response.status_code == 422


async def test_the_address_names_no_teammate(client: AsyncClient) -> None:
    # The guarantee rather than a shorthand: there is no colleague's mailbox
    # this route could reach.
    assert "{" not in URL
    assert URL.endswith("/users/me/reminder-cadence")
