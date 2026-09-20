"""The route that publishes what the register holds on a teammate."""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.users.application.use_cases.get_user_record import GetUserRecordUseCase
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.presentation.dependencies import get_user_record_use_case
from src.shared.utils import clock
from tests.helpers.in_memory_repositories import (
    InMemoryEntryRepository,
    InMemoryMonthRepository,
    InMemoryProjectAssigneeRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
)

TEAMMATE = User(
    id=2,
    entra_oid="oid-2",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)
WAATCHER = Project(
    id=1, label="WAATcher", kind=ProjectKind.PROJECT, status=ProjectStatus.DEVELOPMENT
)

URL = f"{get_settings().api_prefix}/users/2/record"


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_current_user] = lambda: TEAMMATE
    app.dependency_overrides[get_user_record_use_case] = lambda: GetUserRecordUseCase(
        users=InMemoryUserRepository([TEAMMATE]),
        projects=InMemoryProjectRepository([WAATCHER]),
        assignees=InMemoryProjectAssigneeRepository(
            {(WAATCHER.id, ProjectRole.LEAD): [TEAMMATE.id]}
        ),
        entries=InMemoryEntryRepository(
            [
                Entry(
                    id=None,
                    user_id=2,
                    project_id=1,
                    day=clock.today(),
                    value=DayValue(0.5),
                )
            ]
        ),
        months=InMemoryMonthRepository(),
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()


async def test_a_teammate_reads_the_record_of_a_colleague(
    client: AsyncClient,
) -> None:
    """Anyone may look at anyone's month, and at what leads to it."""
    response = await client.get(URL)

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == 2
    assert body["missions"] == [
        {
            "project_id": 1,
            "label": "WAATcher",
            "status": "development",
            "is_lead": True,
        }
    ]


async def test_the_record_publishes_the_window_it_was_read_over(
    client: AsyncClient,
) -> None:
    body = (await client.get(URL)).json()

    assert body["declared"]["until"] == clock.today().isoformat()
    assert body["declared"]["days"] == 0.5
    assert body["declared"]["missions"][0]["label"] == "WAATcher"


async def test_the_record_publishes_six_months_newest_first(
    client: AsyncClient,
) -> None:
    body = (await client.get(URL)).json()

    months = [filling["month"] for filling in body["months"]]
    assert len(months) == 6
    assert months == sorted(months, reverse=True)
    assert months[0] == clock.today().replace(day=1).isoformat()


async def test_an_unknown_teammate_is_a_404(client: AsyncClient) -> None:
    response = await client.get(f"{get_settings().api_prefix}/users/999/record")

    assert response.status_code == 404
