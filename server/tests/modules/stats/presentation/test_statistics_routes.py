"""The statistics route and the contract it publishes."""

from collections.abc import AsyncIterator
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.projects.domain.entities.project import (
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)
from src.modules.stats.application.use_cases.compute_statistics import (
    ComputeStatisticsUseCase,
)
from src.modules.stats.presentation.dependencies import get_compute_statistics_use_case
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryStatisticsRepository,
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
    User(id=2, entra_oid="oid-2", email="b@waat.fr", display_name="B. Cy"),
]


def use_case() -> ComputeStatisticsUseCase:
    return ComputeStatisticsUseCase(
        users=InMemoryUserRepository(TEAM),
        statistics=InMemoryStatisticsRepository(
            declared_by_day={date.today(): 6.0},
            contributors={1},
            delays=[0, 1, 30],
            by_kind={ProjectKind.PROJECT: 4.0, ProjectKind.OFF_PROJECT: 2.0},
            by_status={ProjectStatus.DEVELOPMENT: 3.0, ProjectStatus.SCOPING: 1.0},
            by_category={ProjectCategory.AUTOMATE: 4.0, None: 2.0},
            missions=[(7, "Extranet", 4.0), (9, "Congés", 2.0)],
            active_missions=10,
            missions_with_time=2,
            created=1,
        ),
    )


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_current_user] = lambda: READER
    app.dependency_overrides[get_compute_statistics_use_case] = use_case
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()


URL = f"{get_settings().api_prefix}/stats"


async def test_the_dashboard_answers_a_teammate(client: AsyncClient) -> None:
    # The screen is open to the whole team, not just to managers.
    response = await client.get(URL, params={"range": "last_7_days"})

    assert response.status_code == 200


async def test_the_window_asked_for_comes_back_with_the_figures(
    client: AsyncClient,
) -> None:
    response = await client.get(URL, params={"range": "last_7_days"})

    period = response.json()["period"]
    assert period["range"] == "last_7_days"
    assert period["end"] == date.today().isoformat()


async def test_the_window_defaults_to_the_last_thirty_days(
    client: AsyncClient,
) -> None:
    response = await client.get(URL)

    assert response.json()["period"]["range"] == "last_30_days"


async def test_an_unknown_window_is_refused(client: AsyncClient) -> None:
    response = await client.get(URL, params={"range": "last_year"})

    assert response.status_code == 422


async def test_coverage_comes_with_what_it_is_measured_against(
    client: AsyncClient,
) -> None:
    response = await client.get(URL, params={"range": "today"})

    coverage = response.json()["coverage"]
    assert coverage["declared_days"] == 6.0
    assert "expected_days" in coverage
    assert "rate" in coverage


async def test_teammates_who_declared_nothing_are_named(
    client: AsyncClient,
) -> None:
    response = await client.get(URL, params={"range": "today"})

    assert response.json()["adoption"]["idle"] == [{"id": 2, "display_name": "B. Cy"}]


async def test_phases_are_listed_heaviest_first(client: AsyncClient) -> None:
    response = await client.get(URL, params={"range": "today"})

    by_status = response.json()["steering"]["by_status"]
    assert [row["status"] for row in by_status] == ["development", "scoping"]
    assert by_status[0]["share"] == pytest.approx(0.5)


async def test_a_mission_without_a_strategic_axis_is_reported_apart(
    client: AsyncClient,
) -> None:
    response = await client.get(URL, params={"range": "today"})

    categories = response.json()["steering"]["by_category"]
    assert {row["category"] for row in categories} == {"automate_streamline", None}


async def test_the_heaviest_missions_carry_their_share(client: AsyncClient) -> None:
    response = await client.get(URL, params={"range": "today"})

    top = response.json()["steering"]["top_missions"]
    assert top[0]["label"] == "Extranet"
    assert top[0]["share"] == pytest.approx(4 / 6)


async def test_the_registry_reports_what_nobody_booked_against(
    client: AsyncClient,
) -> None:
    response = await client.get(URL, params={"range": "today"})

    registry = response.json()["registry"]
    assert registry["missions_without_time"] == 8
    assert registry["created"] == 1
