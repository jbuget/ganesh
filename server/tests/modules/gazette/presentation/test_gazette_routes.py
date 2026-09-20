"""The routes that read a month and ask for its digest."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, datetime

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.gazette.application.use_cases.generate_digest import (
    GenerateDigestUseCase,
)
from src.modules.gazette.application.use_cases.read_digest import ReadDigestUseCase
from src.modules.gazette.domain.entities.brief import Brief
from src.modules.gazette.domain.entities.prose import Prose
from src.modules.gazette.domain.repositories.prose_writer import ProseWriter
from src.modules.gazette.presentation.dependencies import (
    get_generate_digest_use_case,
    get_read_digest_use_case,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryDigestRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
)

LEA = User(
    id=1,
    entra_oid="oid-1",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)
GANESH = Project(
    id=7, label="Ganesh", kind=ProjectKind.PROJECT, status=ProjectStatus.DEVELOPMENT
)
MONTH = date(2026, 9, 1)
GAZETTE = f"{get_settings().api_prefix}/gazette"


class StubProseWriter(ProseWriter):
    def __init__(self, text: str | None = "Un mois de cadrage.") -> None:
        self._text = text

    async def write(self, brief: Brief) -> Prose | None:
        return Prose.accepted(self._text, model="stub") if self._text else None


@dataclass
class Screen:
    """A signed-in teammate and the digests their calls land on."""

    client: AsyncClient
    digests: InMemoryDigestRepository
    audit_logs: InMemoryAuditLogRepository

    async def read(self, month: date = MONTH, version: int | None = None):
        params: dict[str, object] = {"month": month.isoformat()}
        if version is not None:
            params["version"] = version
        return await self.client.get(GAZETTE, params=params)

    async def ask_for(self, month: date = MONTH):
        return await self.client.post(GAZETTE, json={"month": month.isoformat()})


def sign_in(writer: ProseWriter | None = None) -> Screen:
    digests = InMemoryDigestRepository()
    audit_logs = InMemoryAuditLogRepository()
    users = InMemoryUserRepository([LEA])
    projects = InMemoryProjectRepository([GANESH])

    app.dependency_overrides[get_current_user] = lambda: LEA
    app.dependency_overrides[get_read_digest_use_case] = lambda: ReadDigestUseCase(
        users=users, projects=projects, audit_logs=audit_logs, digests=digests
    )
    app.dependency_overrides[get_generate_digest_use_case] = (
        lambda: GenerateDigestUseCase(
            users=users,
            projects=projects,
            audit_logs=audit_logs,
            digests=digests,
            writer=writer or StubProseWriter(),
        )
    )
    return Screen(
        client=AsyncClient(transport=ASGITransport(app=app), base_url="http://test"),
        digests=digests,
        audit_logs=audit_logs,
    )


@pytest.fixture(autouse=True)
def _forget_the_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def screen() -> Screen:
    return sign_in()


@pytest.mark.asyncio
async def test_a_month_nobody_asked_for_reads_from_the_register(
    screen: Screen,
) -> None:
    response = await screen.read()

    assert response.status_code == 200
    body = response.json()
    assert body["month"] == "2026-09-01"
    assert body["is_generated"] is False
    assert body["version"] is None
    assert body["prose"] is None
    assert body["versions"] == []
    assert body["chapters"] == []


@pytest.mark.asyncio
async def test_a_teammate_asks_for_a_digest(screen: Screen) -> None:
    """No role is needed: the facts are open to the whole team already."""
    response = await screen.ask_for()

    assert response.status_code == 201
    body = response.json()
    assert body["is_generated"] is True
    assert body["version"] == 1
    assert body["requested_by"] == "L. Chen"
    assert body["generated_at"] is not None
    assert body["prose"] == "Un mois de cadrage."
    assert body["prose_model"] == "stub"


@pytest.mark.asyncio
async def test_asking_again_adds_a_version(screen: Screen) -> None:
    await screen.ask_for()

    response = await screen.ask_for()

    assert response.json()["version"] == 2
    assert [v["version"] for v in response.json()["versions"]] == [2, 1]


@pytest.mark.asyncio
async def test_a_month_reads_as_its_latest_version(screen: Screen) -> None:
    await screen.ask_for()
    await screen.ask_for()

    body = (await screen.read()).json()

    assert body["version"] == 2
    assert [v["version"] for v in body["versions"]] == [2, 1]


@pytest.mark.asyncio
async def test_an_older_version_can_still_be_opened(screen: Screen) -> None:
    await screen.ask_for()
    await screen.ask_for()

    body = (await screen.read(version=1)).json()

    assert body["version"] == 1


@pytest.mark.asyncio
async def test_a_version_nobody_generated_is_not_invented(screen: Screen) -> None:
    await screen.ask_for()

    assert (await screen.read(version=7)).status_code == 404


@pytest.mark.asyncio
async def test_a_version_below_the_first_is_refused(screen: Screen) -> None:
    assert (await screen.read(version=0)).status_code == 422


@pytest.mark.asyncio
async def test_a_month_that_is_not_a_date_is_refused(screen: Screen) -> None:
    response = await screen.client.get(GAZETTE, params={"month": "septembre"})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_the_digest_holds_without_a_chapeau() -> None:
    """A model that says nothing costs the prose, never the facts."""
    screen = sign_in(StubProseWriter(None))

    body = (await screen.ask_for()).json()

    assert body["is_generated"] is True
    assert body["prose"] is None
    assert body["prose_model"] is None


@pytest.mark.asyncio
async def test_the_month_comes_back_gathered_by_mission(screen: Screen) -> None:
    """A flat list would read as the log it came from."""
    await screen.audit_logs.add(
        AuditLog(
            action=AuditAction.PROJECT_CREATE,
            actor_id=1,
            project_id=7,
            at=datetime(2026, 9, 3, 9),
        )
    )

    body = (await screen.read()).json()

    assert [chapter["label"] for chapter in body["chapters"]] == ["Ganesh"]
    assert len(body["chapters"][0]["movements"]) == 1


@pytest.mark.asyncio
async def test_what_was_about_nobody_s_mission_comes_back_unnamed(
    screen: Screen,
) -> None:
    await screen.audit_logs.add(
        AuditLog(
            action=AuditAction.USER_CREATE,
            actor_id=1,
            target_user_id=1,
            at=datetime(2026, 9, 3, 9),
        )
    )

    body = (await screen.read()).json()

    assert body["chapters"][0]["label"] is None
    assert body["chapters"][0]["project_id"] is None
    assert [h["label"] for h in body["highlights"]] == ["L. Chen"]
