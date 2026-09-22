"""Leaving and taking back a sign through the API."""

from collections.abc import Iterator
from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.projects.application.use_cases.project_updates import (
    ListProjectUpdatesUseCase,
    ReactToUpdateUseCase,
    WithdrawReactionUseCase,
)
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.projects.presentation.dependencies import (
    get_list_updates_use_case,
    get_react_to_update_use_case,
    get_withdraw_reaction_use_case,
)
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryProjectUpdateRepository,
    InMemoryUpdateReactionRepository,
    InMemoryUserRepository,
)

ALICE = User(
    id=1,
    entra_oid="oid-1",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)
NINO = User(
    id=2,
    entra_oid="oid-2",
    email="n.garo.ext@waat.fr",
    display_name="N. Garo",
    role=Role.TEAMMATE,
)
WHEN = datetime(2026, 9, 17, 10, 0)
URL = f"{get_settings().api_prefix}/projects"


async def sign_in(as_who: User = NINO) -> tuple[AsyncClient, ProjectUpdate]:
    updates = InMemoryProjectUpdateRepository()
    reactions = InMemoryUpdateReactionRepository()
    posted = await updates.add(
        ProjectUpdate(
            id=None,
            project_id=10,
            author_id=1,
            body="Mise en service vendredi.",
            published_at=WHEN,
        )
    )

    app.dependency_overrides[get_current_user] = lambda: as_who
    app.dependency_overrides[get_react_to_update_use_case] = (
        lambda: ReactToUpdateUseCase(updates, reactions)
    )
    app.dependency_overrides[get_withdraw_reaction_use_case] = (
        lambda: WithdrawReactionUseCase(reactions)
    )
    app.dependency_overrides[get_list_updates_use_case] = (
        lambda: ListProjectUpdatesUseCase(
            updates, InMemoryUserRepository([ALICE, NINO]), reactions
        )
    )
    return (
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test"),
        posted,
    )


@pytest.fixture(autouse=True)
def _forget_the_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


async def test_a_sign_is_left_and_read_back_in_the_thread() -> None:
    client, posted = await sign_in()

    left = await client.put(f"{URL}/10/updates/{posted.id}/reactions/thumbs_up")
    thread = await client.get(f"{URL}/10/updates")

    assert left.status_code == 204
    assert thread.json()[0]["reactions"] == [
        {"reaction": "thumbs_up", "people": ["N. Garo"], "is_mine": True}
    ]


async def test_a_sign_left_by_somebody_else_is_not_mine() -> None:
    client, posted = await sign_in(as_who=ALICE)
    await client.put(f"{URL}/10/updates/{posted.id}/reactions/heart")
    app.dependency_overrides[get_current_user] = lambda: NINO

    thread = await client.get(f"{URL}/10/updates")

    assert thread.json()[0]["reactions"][0]["is_mine"] is False


async def test_a_sign_is_taken_back() -> None:
    client, posted = await sign_in()
    await client.put(f"{URL}/10/updates/{posted.id}/reactions/eyes")

    taken = await client.delete(f"{URL}/10/updates/{posted.id}/reactions/eyes")

    assert taken.status_code == 204
    assert (await client.get(f"{URL}/10/updates")).json()[0]["reactions"] == []


async def test_a_sign_outside_the_set_is_refused() -> None:
    """The set is closed: the API does not take an emoji somebody invented."""
    client, posted = await sign_in()

    refused = await client.put(f"{URL}/10/updates/{posted.id}/reactions/party_parrot")

    assert refused.status_code == 422


async def test_reacting_to_an_unknown_update_is_a_404() -> None:
    client, _ = await sign_in()

    assert (await client.put(f"{URL}/10/updates/999/reactions/eyes")).status_code == 404


async def test_reacting_to_a_withdrawn_update_is_refused() -> None:
    client, posted = await sign_in(as_who=ALICE)
    await client.delete(f"{URL}/10/updates/{posted.id}")
    posted.remove(by=1, at=WHEN)

    refused = await client.put(f"{URL}/10/updates/{posted.id}/reactions/thumbs_up")

    assert refused.status_code == 403
