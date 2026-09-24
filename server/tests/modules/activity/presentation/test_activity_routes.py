"""The activity route and the contract it publishes."""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.activity.application.use_cases.get_activity_summary import (
    GetActivitySummaryUseCase,
)
from src.modules.activity.domain.repositories.activity_repository import (
    DeclaredDays,
    MissionRecord,
)
from src.modules.activity.presentation.dependencies import get_activity_summary_use_case
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.calendar.domain.entities.period import Period, PeriodRange
from src.modules.projects.domain.entities.project import ProjectKind, ProjectStatus
from src.modules.users.domain.entities.user import Role, User
from src.shared.utils import clock
from tests.helpers.in_memory_repositories import (
    InMemoryActivityRepository,
    InMemoryUserRepository,
)

READER = User(
    id=1,
    entra_oid="oid-1",
    email="a@waat.fr",
    display_name="A. Ba",
    role=Role.TEAMMATE,
)
TEAM = [
    READER,
    User(
        id=2,
        entra_oid="oid-2",
        email="b@waat.fr",
        display_name="B. Cy",
        role=Role.TEAMMATE,
    ),
]

MISSIONS = [
    MissionRecord(
        project_id=7,
        label="Extranet",
        kind=ProjectKind.PROJECT,
        status=ProjectStatus.DEVELOPMENT,
        category=None,
        parent_id=None,
    ),
    MissionRecord(
        project_id=8,
        label="Lot API",
        kind=ProjectKind.WORK_PACKAGE,
        status=ProjectStatus.DEVELOPMENT,
        category=None,
        parent_id=7,
    ),
    MissionRecord(
        project_id=9,
        label="Congés",
        kind=ProjectKind.OFF_PROJECT,
        status=None,
        category=None,
        parent_id=None,
    ),
]


def use_case() -> GetActivitySummaryUseCase:
    window = Period.of(PeriodRange.LAST_WEEK, clock.today())
    return GetActivitySummaryUseCase(
        users=InMemoryUserRepository(TEAM),
        activity=InMemoryActivityRepository(
            missions=MISSIONS,
            declared={
                InMemoryActivityRepository.key(window): [
                    DeclaredDays(project_id=7, user_id=1, days=3.0),
                    DeclaredDays(project_id=8, user_id=2, days=1.0),
                    DeclaredDays(project_id=9, user_id=1, days=2.0),
                ]
            },
        ),
    )


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_current_user] = lambda: READER
    app.dependency_overrides[get_activity_summary_use_case] = use_case
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()


URL = f"{get_settings().api_prefix}/activity"


async def test_the_summary_answers_a_teammate(client: AsyncClient) -> None:
    # The screen is open to the whole team, not just to managers.
    response = await client.get(URL, params={"range": "last_week"})

    assert response.status_code == 200


async def test_the_window_asked_for_comes_back_with_the_matrix(
    client: AsyncClient,
) -> None:
    response = await client.get(URL, params={"range": "last_week"})

    assert response.json()["period"]["range"] == "last_week"


async def test_the_window_defaults_to_last_week(client: AsyncClient) -> None:
    # What a Monday-morning reading asks for, and the only default that does
    # not need choosing before the screen opens.
    response = await client.get(URL)

    assert response.json()["period"]["range"] == "last_week"


async def test_the_whole_team_is_named_in_the_columns(client: AsyncClient) -> None:
    response = await client.get(URL, params={"range": "last_week"})

    names = [one["display_name"] for one in response.json()["contributors"]]
    assert names == ["A. Ba", "B. Cy"]


async def test_a_work_package_reads_under_its_project(client: AsyncClient) -> None:
    response = await client.get(URL, params={"range": "last_week"})

    projects = response.json()["projects"]
    assert [line["label"] for line in projects] == ["Extranet"]
    assert [p["label"] for p in projects[0]["packages"]] == ["Lot API"]
    assert projects[0]["days"] == 4.0
    assert projects[0]["own_days"] == 3.0


async def test_off_project_work_is_answered_apart(client: AsyncClient) -> None:
    body = (await client.get(URL, params={"range": "last_week"})).json()

    assert [line["label"] for line in body["off_project"]] == ["Congés"]
    assert body["project_days"] == 4.0
    assert body["off_project_days"] == 2.0
    assert body["declared_days"] == 6.0


async def test_a_cell_carries_the_days_of_the_person_who_booked_them(
    client: AsyncClient,
) -> None:
    body = (await client.get(URL, params={"range": "last_week"})).json()

    extranet = body["projects"][0]
    # Rolled up: 3 days of A. Ba on the project, 1 of B. Cy on its package.
    assert extranet["days_by_contributor"] == {"1": 3.0, "2": 1.0}


async def test_an_unknown_window_is_refused(client: AsyncClient) -> None:
    response = await client.get(URL, params={"range": "la-semaine-derniere"})

    assert response.status_code == 422


async def test_a_project_answers_for_its_own_days_apart_from_its_packages(
    client: AsyncClient,
) -> None:
    # Unfolded, the project's own row must read what was booked on it
    # directly — never the total a second time.
    body = (await client.get(URL, params={"range": "last_week"})).json()

    extranet = body["projects"][0]
    assert extranet["own_days_by_contributor"] == {"1": 3.0}
    assert extranet["packages"][0]["own_days_by_contributor"] == {"2": 1.0}
