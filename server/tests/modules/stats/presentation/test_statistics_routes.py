"""The statistics route and the contract it publishes."""

from collections.abc import AsyncIterator
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.api_keys.presentation.dependencies import teammate_or_machine
from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.projects.domain.entities.project import (
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)
from src.modules.stats.application.use_cases.compute_statistics import (
    ComputeStatisticsUseCase,
)
from src.modules.stats.domain.entities.surface_usage import Surface, Tally, Trace
from src.modules.stats.presentation.dependencies import get_compute_statistics_use_case
from src.modules.users.domain.entities.user import Role, User
from src.shared.utils import clock
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
    User(
        id=2,
        entra_oid="oid-2",
        email="b@waat.fr",
        display_name="B. Cy",
        role=Role.TEAMMATE,
    ),
]


def use_case() -> ComputeStatisticsUseCase:
    return ComputeStatisticsUseCase(
        users=InMemoryUserRepository(TEAM),
        statistics=InMemoryStatisticsRepository(
            declared_by_day={clock.today(): 6.0},
            contributors={1},
            delays=[0, 1, 30],
            by_kind={ProjectKind.PROJECT: 4.0, ProjectKind.OFF_PROJECT: 2.0},
            by_status={ProjectStatus.DEVELOPMENT: 3.0, ProjectStatus.SCOPING: 1.0},
            by_category={ProjectCategory.AUTOMATE: 4.0, None: 2.0},
            missions=[(7, "Extranet", 4.0), (9, "Congés", 2.0)],
            active_missions=10,
            missions_with_time=2,
            created=1,
            traces={
                clock.today(): [
                    Trace(AuditAction.ENTRY_SET, actor_id=1, gestures=4),
                    Trace(AuditAction.GAZETTE_GENERATE, actor_id=2, gestures=1),
                ]
            },
            tallies={clock.today(): {Surface.MOOD: Tally(people=2, gestures=5)}},
            last_gestures={AuditAction.PROJECT_CREATE: date(2026, 6, 4)},
        ),
    )


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[teammate_or_machine] = lambda: READER
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
    assert period["end"] == clock.today().isoformat()


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


async def test_every_function_of_the_product_is_read(client: AsyncClient) -> None:
    # A function missing from the table would pass for one that is doing
    # fine: they all get their line, used or not.
    response = await client.get(URL, params={"range": "today"})

    surfaces = response.json()["surfaces"]["activities"]
    assert [row["surface"] for row in surfaces] == list(Surface)


async def test_a_function_says_who_used_it_and_how_much(client: AsyncClient) -> None:
    response = await client.get(URL, params={"range": "today"})

    rows = {row["surface"]: row for row in response.json()["surfaces"]["activities"]}
    assert (rows["time_entry"]["people"], rows["time_entry"]["gestures"]) == (1, 4)
    assert (rows["mood"]["people"], rows["mood"]["gestures"]) == (2, 5)


async def test_a_function_nobody_used_lately_still_carries_its_last_day(
    client: AsyncClient,
) -> None:
    response = await client.get(URL, params={"range": "today"})

    rows = {row["surface"]: row for row in response.json()["surfaces"]["activities"]}
    assert rows["project_registry"]["gestures"] == 0
    assert rows["project_registry"]["last_used_on"] == "2026-06-04"
    assert rows["assignment"]["last_used_on"] is None


async def test_the_table_counts_what_served_nobody(client: AsyncClient) -> None:
    response = await client.get(URL, params={"range": "today"})

    # Three of them saw something today: the grid, the gazette and the moods.
    assert response.json()["surfaces"]["idle_count"] == len(Surface) - 3


async def test_a_function_says_itself_whether_it_served_anybody(
    client: AsyncClient,
) -> None:
    # The screen must not work the rule out a second time: the count of idle
    # functions and the mark on a line read the same one.
    response = await client.get(URL, params={"range": "today"})

    rows = {row["surface"]: row for row in response.json()["surfaces"]["activities"]}
    assert rows["time_entry"]["is_idle"] is False
    assert rows["planning"]["is_idle"] is True
