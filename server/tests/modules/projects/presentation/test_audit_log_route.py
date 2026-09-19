"""Reading a mission's log through the API."""

from collections.abc import Iterator
from datetime import date, datetime

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.audit_logs.application.use_cases.list_project_audit_log import (
    ListProjectAuditLogUseCase,
)
from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.presentation.dependencies import (
    get_project_audit_log_use_case,
)
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryUserRepository,
)

ALICE = User(
    id=1,
    entra_oid="oid-1",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    first_name="Lin",
    last_name="Chen",
    role=Role.TEAMMATE,
)

URL = f"{get_settings().api_prefix}/projects"


def sign_in(logs: list[AuditLog]) -> AsyncClient:
    audit = InMemoryAuditLogRepository()
    for log in logs:
        log.id = len(audit.logs) + 1
        audit.logs.append(log)

    app.dependency_overrides[get_current_user] = lambda: ALICE
    app.dependency_overrides[get_project_audit_log_use_case] = (
        lambda: ListProjectAuditLogUseCase(
            audit_logs=audit, users=InMemoryUserRepository([ALICE])
        )
    )
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture(autouse=True)
def _forget_the_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


async def test_the_log_of_a_mission_is_served_signed_and_most_recent_first() -> None:
    client = sign_in(
        [
            AuditLog(
                action=AuditAction.PROJECT_CREATE,
                actor_id=1,
                project_id=10,
                at=datetime(2026, 9, 1, 9, 0),
            ),
            AuditLog(
                action=AuditAction.ENTRY_SET,
                actor_id=1,
                target_user_id=1,
                project_id=10,
                day=date(2026, 9, 14),
                old_value="0.5",
                new_value="1.0",
                at=datetime(2026, 9, 14, 11, 30),
            ),
        ]
    )

    response = await client.get(f"{URL}/10/audit")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    first, second = body["entries"]
    assert first["action"] == "entry.set"
    assert first["day"] == "2026-09-14"
    assert first["old_value"] == "0.5" and first["new_value"] == "1.0"
    assert first["actor"] == {"id": 1, "display_name": "Lin Chen", "initials": "LC"}
    assert first["target_user"]["id"] == 1
    assert second["action"] == "project.create"
    assert second["target_user"] is None


async def test_the_log_names_the_field_a_gesture_moved() -> None:
    client = sign_in(
        [
            AuditLog(
                action=AuditAction.PROJECT_UPDATE,
                actor_id=1,
                project_id=10,
                old_value="EDIT",
                new_value="EDIT v2",
                payload={"field": "label"},
                at=datetime(2026, 9, 2, 9, 0),
            )
        ]
    )

    response = await client.get(f"{URL}/10/audit")

    assert response.json()["entries"][0]["field"] == "label"


async def test_the_log_is_read_one_page_at_a_time() -> None:
    client = sign_in(
        [
            AuditLog(
                action=AuditAction.PROJECT_UPDATE,
                actor_id=1,
                project_id=10,
                at=datetime(2026, 9, day, 9, 0),
            )
            for day in range(1, 6)
        ]
    )

    response = await client.get(f"{URL}/10/audit", params={"limit": 2, "offset": 2})

    body = response.json()
    assert len(body["entries"]) == 2
    # The count stays that of the whole log: it is what says there is more.
    assert body["total"] == 5


async def test_a_mission_nothing_ever_happened_to_answers_an_empty_log() -> None:
    client = sign_in([])

    response = await client.get(f"{URL}/999/audit")

    assert response.status_code == 200
    assert response.json() == {"total": 0, "entries": []}
