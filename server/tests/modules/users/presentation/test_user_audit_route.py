"""The route that publishes one teammate's log."""

from collections.abc import AsyncIterator
from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.audit_logs.application.use_cases.list_user_audit_log import (
    ListUserAuditLogUseCase,
)
from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.presentation.dependencies import get_user_audit_log_use_case
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.utils import clock
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
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
MANAGER = User(
    id=3,
    entra_oid="oid-3",
    email="n.garo@waat.fr",
    display_name="N. Garo",
    role=Role.MANAGER,
)
WAATCHER = Project(
    id=10, label="WAATcher", kind=ProjectKind.PROJECT, status=ProjectStatus.DEVELOPMENT
)

URL = f"{get_settings().api_prefix}/users/2/audit"


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    audit = InMemoryAuditLogRepository()
    audit.logs = [
        AuditLog(
            id=1,
            action=AuditAction.PROJECT_CREATE,
            actor_id=2,
            project_id=10,
            at=clock.as_instant(datetime(2026, 9, 1, 9, 0)),
        ),
        AuditLog(
            id=2,
            action=AuditAction.USER_ROLE_CHANGE,
            actor_id=3,
            target_user_id=2,
            old_value="teammate",
            new_value="manager",
            at=clock.as_instant(datetime(2026, 9, 2, 9, 0)),
        ),
        AuditLog(
            id=3,
            action=AuditAction.PROJECT_CREATE,
            actor_id=3,
            project_id=10,
            at=clock.as_instant(datetime(2026, 9, 3, 9, 0)),
        ),
    ]
    app.dependency_overrides[get_current_user] = lambda: TEAMMATE
    app.dependency_overrides[get_user_audit_log_use_case] = (
        lambda: ListUserAuditLogUseCase(
            audit_logs=audit,
            users=InMemoryUserRepository([TEAMMATE, MANAGER]),
            projects=InMemoryProjectRepository([WAATCHER]),
        )
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()


async def test_a_teammate_reads_the_log_of_a_colleague(client: AsyncClient) -> None:
    """Open to the whole team, like the record beside it."""
    response = await client.get(URL)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert [entry["action"] for entry in body["entries"]] == [
        "user.role_change",
        "project.create",
    ]


async def test_every_line_names_its_mission(client: AsyncClient) -> None:
    """The panel is a person: an unplaced gesture names nothing."""
    body = (await client.get(URL)).json()

    created = body["entries"][1]
    assert created["project"]["label"] == "WAATcher"
    assert created["actor"]["display_name"] == "L. Chen"


async def test_the_log_is_read_page_by_page(client: AsyncClient) -> None:
    body = (await client.get(f"{URL}?limit=1&offset=1")).json()

    assert [entry["action"] for entry in body["entries"]] == ["project.create"]
    # The count is of the whole log: it is what says there is more to fetch.
    assert body["total"] == 2
