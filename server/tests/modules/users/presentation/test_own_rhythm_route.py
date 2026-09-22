"""The route by which everyone declares their own rhythm, and no one else's."""

from collections.abc import AsyncIterator
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.calendar.domain.entities.week_pattern import WeekPattern
from src.modules.users.application.use_cases.declare_own_rhythm import (
    DeclareOwnRhythmUseCase,
)
from src.modules.users.application.use_cases.withdraw_own_rhythm import (
    WithdrawOwnRhythmUseCase,
)
from src.modules.users.domain.entities.rhythm import Rhythm
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.presentation.dependencies import (
    get_declare_own_rhythm_use_case,
    get_withdraw_own_rhythm_use_case,
)
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryRhythmRepository,
    InMemoryUserRepository,
)

TEAMMATE = User(
    id=2,
    entra_oid="oid-2",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)

URL = f"{get_settings().api_prefix}/users/me/rhythm"

FOUR_FIFTHS = {
    "effective_from": "2026-09-01",
    "monday": 1.0,
    "tuesday": 1.0,
    "wednesday": 0.0,
    "thursday": 1.0,
    "friday": 1.0,
}


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    users = InMemoryUserRepository([TEAMMATE])
    rhythms = InMemoryRhythmRepository(
        [
            Rhythm(
                id=None,
                user_id=2,
                pattern=WeekPattern(wednesday=0.0),
                effective_from=date(2026, 10, 5),
            )
        ]
    )
    app.dependency_overrides[get_current_user] = lambda: TEAMMATE
    app.dependency_overrides[get_declare_own_rhythm_use_case] = (
        lambda: DeclareOwnRhythmUseCase(
            users=users,
            rhythms=rhythms,
            audit_logs=InMemoryAuditLogRepository(),
        )
    )
    app.dependency_overrides[get_withdraw_own_rhythm_use_case] = (
        lambda: WithdrawOwnRhythmUseCase(
            users=users,
            rhythms=rhythms,
            audit_logs=InMemoryAuditLogRepository(),
        )
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()


async def test_a_teammate_declares_their_rhythm(client: AsyncClient) -> None:
    response = await client.put(URL, json=FOUR_FIFTHS)

    assert response.status_code == 200
    body = response.json()
    assert body["wednesday"] == 0.0
    assert body["effective_from"] == "2026-09-01"


async def test_the_week_is_counted_by_the_api(client: AsyncClient) -> None:
    # Two screens counting it themselves would count it differently.
    response = await client.put(URL, json=FOUR_FIFTHS)

    assert response.json()["days_per_week"] == 4.0


async def test_a_half_day_is_a_rhythm_like_any_other(client: AsyncClient) -> None:
    response = await client.put(URL, json={**FOUR_FIFTHS, "wednesday": 0.5})

    assert response.status_code == 200
    assert response.json()["days_per_week"] == 4.5


async def test_a_day_worth_anything_else_is_refused(client: AsyncClient) -> None:
    response = await client.put(URL, json={**FOUR_FIFTHS, "monday": 0.8})

    assert response.status_code == 422


async def test_a_rhythm_expecting_nothing_is_refused(client: AsyncClient) -> None:
    # Expecting nothing of somebody is what deactivating their account says.
    response = await client.put(
        URL,
        json={
            "effective_from": "2026-09-01",
            "monday": 0.0,
            "tuesday": 0.0,
            "wednesday": 0.0,
            "thursday": 0.0,
            "friday": 0.0,
        },
    )

    assert response.status_code == 422


async def test_there_is_no_route_to_declare_for_somebody_else(
    client: AsyncClient,
) -> None:
    # The guarantee is the shape of the address: no id to pass, no colleague
    # to reach by mistake.
    response = await client.put(
        f"{get_settings().api_prefix}/users/2/rhythm", json=FOUR_FIFTHS
    )

    assert response.status_code == 404


async def test_a_teammate_takes_one_of_their_rhythms_back_out(
    client: AsyncClient,
) -> None:
    response = await client.delete(f"{URL}/2026-10-05")

    assert response.status_code == 204


async def test_withdrawing_a_rhythm_that_is_not_there_is_a_404(
    client: AsyncClient,
) -> None:
    # Silence would read as a withdrawal, and the screen would stop showing a
    # row the register still holds.
    response = await client.delete(f"{URL}/2026-01-01")

    assert response.status_code == 404


async def test_there_is_no_route_to_withdraw_for_somebody_else(
    client: AsyncClient,
) -> None:
    response = await client.delete(
        f"{get_settings().api_prefix}/users/2/rhythm/2026-10-05"
    )

    assert response.status_code == 404
