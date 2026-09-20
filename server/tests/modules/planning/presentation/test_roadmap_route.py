"""The roadmap route: the window it reads, and what it publishes."""

from collections.abc import AsyncIterator
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.planning.application.use_cases.get_roadmap import GetRoadmapUseCase
from src.modules.planning.presentation.dependencies import get_roadmap_use_case
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.users.domain.entities.user import Role, User
from src.shared.enums.department import Department
from tests.helpers.in_memory_repositories import (
    InMemoryEntryRepository,
    InMemoryProjectAssigneeRepository,
    InMemoryProjectDetailRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
)

ALICE = User(
    id=1,
    entra_oid="oid-1",
    email="alice@waat.fr",
    display_name="Alice",
    role=Role.TEAMMATE,
)
PORTAL = Project(
    id=10,
    label="Portail bailleurs",
    kind=ProjectKind.PROJECT,
    status=ProjectStatus.DEVELOPMENT,
    estimated_days=8.0,
    go_live_date=date(2026, 11, 30),
)

URL = f"{get_settings().api_prefix}/planning/roadmap"


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    details = InMemoryProjectDetailRepository()
    await details.mark_phase_reached(10, ProjectStatus.DEVELOPMENT, date(2026, 5, 4))
    await details.set_departments(10, [Department.LANDLORDS])

    assignees = InMemoryProjectAssigneeRepository()
    await assignees.assign(10, 1, ProjectRole.CONTRIBUTOR)

    entries = InMemoryEntryRepository(
        [
            Entry(
                id=None,
                user_id=1,
                project_id=10,
                day=date(2026, 5, 4),
                value=DayValue(1.0),
                status_at_entry=ProjectStatus.DEVELOPMENT,
            )
        ]
    )

    app.dependency_overrides[get_current_user] = lambda: ALICE
    app.dependency_overrides[get_roadmap_use_case] = lambda: GetRoadmapUseCase(
        projects=InMemoryProjectRepository([PORTAL]),
        entries=entries,
        details=details,
        assignees=assignees,
        users=InMemoryUserRepository([ALICE]),
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()


async def test_the_roadmap_rolls_from_the_month_before_when_asked_for_nothing(
    client: AsyncClient,
) -> None:
    response = await client.get(URL)

    assert response.status_code == 200
    body = response.json()
    # A rolling window always opens on the first of a month and closes on the
    # last of one: the scale draws whole columns.
    assert body["from_day"].endswith("-01")
    assert body["from_day"] < body["today"] <= body["to_day"]


async def test_a_span_says_how_far_ahead_to_look(client: AsyncClient) -> None:
    quarter = (await client.get(URL, params={"months": 3})).json()
    year = (await client.get(URL, params={"months": 12})).json()

    assert quarter["to_day"] < year["to_day"]


async def test_a_span_nobody_could_read_a_bar_in_is_refused(
    client: AsyncClient,
) -> None:
    response = await client.get(URL, params={"months": 99})

    assert response.status_code == 422


async def test_a_window_is_read_from_the_query_string(client: AsyncClient) -> None:
    response = await client.get(
        URL, params={"from_day": "2026-01-01", "to_day": "2026-06-30"}
    )

    assert response.status_code == 200
    assert response.json()["to_day"] == "2026-06-30"


async def test_a_window_read_upside_down_is_refused(client: AsyncClient) -> None:
    response = await client.get(
        URL, params={"from_day": "2026-12-31", "to_day": "2026-01-01"}
    )

    assert response.status_code == 422


async def test_a_line_publishes_its_bar_and_what_it_promised(
    client: AsyncClient,
) -> None:
    response = await client.get(
        URL, params={"from_day": "2026-01-01", "to_day": "2026-12-31"}
    )

    [line] = response.json()["missions"]
    assert line["label"] == "Portail bailleurs"
    assert line["target_date"] == "2026-11-30"
    assert [segment["kind"] for segment in line["segments"]] == ["lived", "projected"]


async def test_the_tally_comes_with_the_drawing(client: AsyncClient) -> None:
    response = await client.get(URL)

    assert response.json()["summary"]["missions"] == 1


class TestNarrowingFromTheQueryString:
    """The criteria are named as the kanban names them: one vocabulary."""

    async def test_a_phase_asked_for_leaves_the_other_lines_out(
        self, client: AsyncClient
    ) -> None:
        response = await client.get(URL, params={"phase": "operations"})

        assert response.status_code == 200
        assert response.json()["missions"] == []

    async def test_the_tally_speaks_of_what_was_kept(self, client: AsyncClient) -> None:
        # The whole reason the narrowing happens here: the figures above the
        # bars must count the bars below them.
        response = await client.get(URL, params={"phase": "operations"})

        assert response.json()["summary"]["missions"] == 0

    async def test_repeating_a_criterion_adds_a_value_to_it(
        self, client: AsyncClient
    ) -> None:
        response = await client.get(URL, params={"phase": ["scoping", "development"]})

        assert len(response.json()["missions"]) == 1

    async def test_a_department_keeps_the_missions_serving_it(
        self, client: AsyncClient
    ) -> None:
        served = await client.get(URL, params={"department": "landlords"})
        elsewhere = await client.get(URL, params={"department": "condominium"})

        assert len(served.json()["missions"]) == 1
        assert elsewhere.json()["missions"] == []

    async def test_a_name_is_searched_without_case_or_accents(
        self, client: AsyncClient
    ) -> None:
        response = await client.get(URL, params={"name": "BAILLEURS"})

        assert len(response.json()["missions"]) == 1

    async def test_a_criterion_nobody_knows_how_to_read_is_refused(
        self, client: AsyncClient
    ) -> None:
        response = await client.get(URL, params={"phase": "recette"})

        assert response.status_code == 422
