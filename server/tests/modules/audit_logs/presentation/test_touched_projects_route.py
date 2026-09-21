"""The shortcut a screen asks the register for."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient

import src.main  # noqa: F401  — imported for the doors it wires at import time
from src.core.config import get_settings
from src.main import app
from src.modules.audit_logs.application.dtos.audit_log_dto import TouchedProject
from src.modules.audit_logs.application.use_cases.list_touched_projects import (
    ListTouchedProjectsUseCase,
)
from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.audit_logs.presentation.dependencies import (
    get_touched_projects_use_case,
)
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.users.domain.entities.user import Role, User

URL = f"{get_settings().api_prefix}/audit-logs/touched-projects"
NOON = datetime(2026, 9, 21, 12, 0, tzinfo=UTC)
LEA = User(
    id=1,
    entra_oid="oid-1",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)


class SpyUseCase(ListTouchedProjectsUseCase):
    """Reads nothing; remembers how many were asked for."""

    def __init__(self) -> None:
        self.limit: int | None = None

    async def execute(self, limit: int) -> list[TouchedProject]:
        self.limit = limit
        return [
            TouchedProject(
                project_id=12, action=AuditAction.PROJECT_STATUS_CHANGE, at=NOON
            )
        ]


@pytest.fixture
async def spy() -> AsyncIterator[SpyUseCase]:
    use_case = SpyUseCase()
    app.dependency_overrides[get_current_user] = lambda: LEA
    app.dependency_overrides[get_touched_projects_use_case] = lambda: use_case
    yield use_case
    app.dependency_overrides.clear()


@pytest.fixture
async def http() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_names_the_project_the_gesture_and_the_moment(
    http: AsyncClient, spy: SpyUseCase
) -> None:
    response = await http.get(URL)

    assert response.status_code == 200
    assert response.json() == [
        {
            "project_id": 12,
            "action": "project.status_change",
            "at": "2026-09-21T12:00:00Z",
        }
    ]


@pytest.mark.asyncio
async def test_asks_for_five_unless_told_otherwise(
    http: AsyncClient, spy: SpyUseCase
) -> None:
    await http.get(URL)

    assert spy.limit == 5


@pytest.mark.asyncio
async def test_carries_the_number_asked_for(http: AsyncClient, spy: SpyUseCase) -> None:
    await http.get(URL, params={"limit": 3})

    assert spy.limit == 3


@pytest.mark.asyncio
async def test_refuses_a_number_the_shortcut_has_no_use_for(
    http: AsyncClient, spy: SpyUseCase
) -> None:
    assert (await http.get(URL, params={"limit": 0})).status_code == 422
    assert (await http.get(URL, params={"limit": 500})).status_code == 422
