"""Archiving a mission: one gesture, and what it asks of a project's slices."""

from collections.abc import Iterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.core.database import get_db
from src.main import app
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.projects.application.use_cases.archive_project import (
    ArchiveProjectUseCase,
    UnarchiveProjectUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.presentation.dependencies import (
    get_archive_project_use_case,
    get_unarchive_project_use_case,
)
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
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

URL = f"{get_settings().api_prefix}/projects"


class FakeSession:
    """Only what the routes ask of a session: that it be committed."""

    async def commit(self) -> None:
        return None


def edit() -> Project:
    return Project(
        id=10,
        label="EDIT",
        kind=ProjectKind.PROJECT,
        status=ProjectStatus.DEVELOPMENT,
    )


def lot() -> Project:
    return Project(
        id=20,
        label="EDIT — Lot 1",
        kind=ProjectKind.WORK_PACKAGE,
        status=ProjectStatus.DEVELOPMENT,
        parent_id=10,
    )


def sign_in(projects: list[Project]) -> tuple[AsyncClient, InMemoryProjectRepository]:
    repo = InMemoryProjectRepository(projects)
    users = InMemoryUserRepository([ALICE])
    audit = InMemoryAuditLogRepository()

    app.dependency_overrides[get_current_user] = lambda: ALICE
    app.dependency_overrides[get_db] = FakeSession
    app.dependency_overrides[get_archive_project_use_case] = (
        lambda: ArchiveProjectUseCase(users=users, projects=repo, audit_logs=audit)
    )
    app.dependency_overrides[get_unarchive_project_use_case] = (
        lambda: UnarchiveProjectUseCase(users=users, projects=repo, audit_logs=audit)
    )
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    return client, repo


@pytest.fixture(autouse=True)
def _forget_the_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


async def test_a_mission_on_its_own_is_archived_without_a_word() -> None:
    client, repo = sign_in([edit()])

    response = await client.post(f"{URL}/10/archive", json={})

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert response.json()["archived_at"] is not None
    mission = await repo.get_by_id(10)
    assert mission is not None and mission.is_active is False


async def test_a_project_cut_into_packages_is_refused_a_silent_exit() -> None:
    client, repo = sign_in([edit(), lot()])

    response = await client.post(f"{URL}/10/archive", json={})

    assert response.status_code == 422
    assert "sub-project" in response.json()["detail"]
    mission = await repo.get_by_id(10)
    assert mission is not None and mission.is_active is True


async def test_the_packages_may_leave_with_their_project() -> None:
    client, repo = sign_in([edit(), lot()])

    response = await client.post(f"{URL}/10/archive", json={"sub_projects": "archive"})

    assert response.status_code == 200
    package = await repo.get_by_id(20)
    assert package is not None and package.is_active is False


async def test_the_packages_may_carry_on_as_projects_of_their_own() -> None:
    client, repo = sign_in([edit(), lot()])

    response = await client.post(f"{URL}/10/archive", json={"sub_projects": "detach"})

    assert response.status_code == 200
    package = await repo.get_by_id(20)
    assert package is not None
    assert package.is_active is True
    assert package.kind is ProjectKind.PROJECT
    assert package.parent_id is None


async def test_an_answer_the_reference_list_does_not_know_is_refused() -> None:
    client, _ = sign_in([edit(), lot()])

    response = await client.post(f"{URL}/10/archive", json={"sub_projects": "delete"})

    assert response.status_code == 422


async def test_a_mission_comes_back_into_the_reference_list() -> None:
    gone = edit()
    gone.archive()
    client, repo = sign_in([gone])

    response = await client.post(f"{URL}/10/unarchive")

    assert response.status_code == 200
    assert response.json()["is_active"] is True
    assert response.json()["archived_at"] is None
    mission = await repo.get_by_id(10)
    assert mission is not None and mission.is_active is True


async def test_an_unknown_mission_is_refused() -> None:
    client, _ = sign_in([edit()])

    response = await client.post(f"{URL}/999/archive", json={})

    assert response.status_code == 404
