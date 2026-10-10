"""Following a mission, and lowering the mark, through the API."""

from collections.abc import Iterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.core.database import get_db
from src.main import app
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.projects.application.use_cases.follow_project import (
    FollowProjectUseCase,
    UnfollowProjectUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.presentation.dependencies import (
    get_follow_project_use_case,
    get_unfollow_project_use_case,
)
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
)

NINO = User(
    id=2,
    entra_oid="oid-2",
    email="n.garo@waat.fr",
    display_name="N. Garo",
    role=Role.TEAMMATE,
)
URL = f"{get_settings().api_prefix}/projects"


class FakeSession:
    """Only what the routes ask of a session: that it be committed."""

    async def commit(self) -> None:
        return None


def sign_in() -> AsyncClient:
    projects = InMemoryProjectRepository(
        [
            Project(
                id=10,
                label="Portail",
                kind=ProjectKind.PROJECT,
                status=ProjectStatus.DEVELOPMENT,
            ),
            Project(id=12, label="Absences", kind=ProjectKind.OFF_PROJECT, status=None),
        ]
    )
    users = InMemoryUserRepository([NINO])
    audit = InMemoryAuditLogRepository()

    app.dependency_overrides[get_current_user] = lambda: NINO
    app.dependency_overrides[get_db] = FakeSession
    app.dependency_overrides[get_follow_project_use_case] = (
        lambda: FollowProjectUseCase(users=users, projects=projects, audit_logs=audit)
    )
    app.dependency_overrides[get_unfollow_project_use_case] = (
        lambda: UnfollowProjectUseCase(users=users, projects=projects, audit_logs=audit)
    )
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture(autouse=True)
def _forget_the_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


async def test_following_a_mission_says_it_is_followed() -> None:
    client = sign_in()

    followed = await client.put(f"{URL}/10/follow")

    assert followed.status_code == 200
    assert followed.json()["is_followed"] is True


async def test_unfollowing_lowers_the_mark() -> None:
    client = sign_in()
    await client.put(f"{URL}/10/follow")

    lowered = await client.delete(f"{URL}/10/follow")

    assert lowered.status_code == 200
    assert lowered.json()["is_followed"] is False


async def test_following_off_project_work_is_refused() -> None:
    client = sign_in()

    assert (await client.put(f"{URL}/12/follow")).status_code == 422


async def test_following_an_unknown_mission_is_a_404() -> None:
    client = sign_in()

    assert (await client.put(f"{URL}/404/follow")).status_code == 404
