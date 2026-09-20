"""The window a machine pulls the log through."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient

import src.main  # noqa: F401  — imported for the doors it wires at import time
from src.core.config import get_settings
from src.main import app
from src.modules.audit_logs.application.use_cases.list_audit_log import (
    AuditLogPage,
    ListAuditLogUseCase,
)
from src.modules.audit_logs.presentation.api.routes.audit_log_router import audit_reader
from src.modules.audit_logs.presentation.dependencies import get_audit_log_use_case

URL = f"{get_settings().api_prefix}/audit-logs"


class SpyUseCase(ListAuditLogUseCase):
    """Reads nothing; remembers the window it was handed."""

    def __init__(self) -> None:
        self.since: datetime | None = None

    async def execute(
        self, limit: int, offset: int, since: datetime | None = None
    ) -> AuditLogPage:
        self.since = since
        return AuditLogPage(entries=[], total=0)


@pytest.fixture
async def spy() -> AsyncIterator[SpyUseCase]:
    use_case = SpyUseCase()
    app.dependency_overrides[audit_reader] = lambda: None
    app.dependency_overrides[get_audit_log_use_case] = lambda: use_case
    yield use_case
    app.dependency_overrides.clear()


@pytest.fixture
async def http() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_a_window_stated_without_a_zone_is_read_on_the_paris_clock(
    http: AsyncClient, spy: SpyUseCase
) -> None:
    # Ten in the morning is what the caller was looking at; the host's own
    # clock is nobody's, and reading it there would skip two hours of log.
    response = await http.get(URL, params={"since": "2026-07-20T10:00:00"})

    assert response.status_code == 200
    assert spy.since == datetime(2026, 7, 20, 8, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_a_window_that_states_its_zone_is_taken_at_its_word(
    http: AsyncClient, spy: SpyUseCase
) -> None:
    response = await http.get(URL, params={"since": "2026-07-20T10:00:00Z"})

    assert response.status_code == 200
    assert spy.since == datetime(2026, 7, 20, 10, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_no_window_asked_for_reads_the_whole_log(
    http: AsyncClient, spy: SpyUseCase
) -> None:
    response = await http.get(URL)

    assert response.status_code == 200
    assert spy.since is None
