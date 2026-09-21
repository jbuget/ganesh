"""Reading back the life of a month."""

from collections.abc import AsyncIterator
from datetime import date, datetime

import pytest
from httpx import ASGITransport, AsyncClient

import src.main  # noqa: F401  — imported for the doors it wires at import time
from src.core.config import get_settings
from src.main import app
from src.modules.audit_logs.application.dtos.audit_log_dto import (
    AuditLogPage,
    SignedAuditLog,
)
from src.modules.audit_logs.application.use_cases.list_month_audit_log import (
    ListMonthAuditLogUseCase,
)
from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.presentation.dependencies import (
    get_month_audit_log_use_case,
)
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.projects.domain.entities.project import Project, ProjectKind
from src.modules.users.domain.entities.user import Role, User

URL = f"{get_settings().api_prefix}/months/2026-09-01/audit"

ALICE = User(
    id=1,
    entra_oid="oid-1",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)
WAATCHER = Project(id=10, label="WAATcher", kind=ProjectKind.PROJECT)


class SpyUseCase(ListMonthAuditLogUseCase):
    """Reads nothing; remembers whose month it was asked for."""

    def __init__(self) -> None:
        self.asked: tuple[int, date, int, int] | None = None

    async def execute(
        self, target_user_id: int, month: date, limit: int, offset: int
    ) -> AuditLogPage:
        self.asked = (target_user_id, month, limit, offset)
        return AuditLogPage(
            entries=[
                SignedAuditLog(
                    log=AuditLog(
                        id=1,
                        action=AuditAction.ENTRY_SET,
                        actor_id=1,
                        target_user_id=1,
                        project_id=10,
                        day=date(2026, 9, 3),
                        at=datetime(2026, 9, 3, 9, 0),
                        new_value="1.0",
                    ),
                    actor=ALICE,
                    target_user=ALICE,
                    project=WAATCHER,
                )
            ],
            total=1,
        )


@pytest.fixture
async def spy() -> AsyncIterator[SpyUseCase]:
    use_case = SpyUseCase()
    app.dependency_overrides[get_current_user] = lambda: ALICE
    app.dependency_overrides[get_month_audit_log_use_case] = lambda: use_case
    yield use_case
    app.dependency_overrides.clear()


@pytest.fixture
async def http() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_the_month_audit_reads_the_month_and_the_person_asked_for(
    http: AsyncClient, spy: SpyUseCase
) -> None:
    response = await http.get(URL, params={"user_id": 1, "limit": 20, "offset": 40})

    assert response.status_code == 200
    assert spy.asked == (1, date(2026, 9, 1), 20, 40)


@pytest.mark.asyncio
async def test_the_month_audit_names_the_mission_each_line_is_about(
    http: AsyncClient, spy: SpyUseCase
) -> None:
    """Out of its grid, a declaration no longer says what it was booked on."""
    response = await http.get(URL, params={"user_id": 1})

    entry = response.json()["entries"][0]
    assert entry["project"] == {"id": 10, "label": "WAATcher"}


@pytest.mark.asyncio
async def test_the_month_audit_is_read_by_the_whole_team(
    http: AsyncClient, spy: SpyUseCase
) -> None:
    """Anyone may edit a colleague's open month; anyone may read what was done."""
    response = await http.get(URL, params={"user_id": 2})

    assert response.status_code == 200
    assert spy.asked is not None and spy.asked[0] == 2
