"""Tags on missions, and the vocabulary, through the API."""

from collections.abc import Iterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.core.database import get_db
from src.main import app
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.projects.application.use_cases.manage_tags import (
    ListTagsUseCase,
    MergeTagsUseCase,
    RecolorTagUseCase,
    RenameTagUseCase,
)
from src.modules.projects.application.use_cases.tag_project import (
    TagProjectUseCase,
    UntagProjectUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.presentation.dependencies import (
    get_list_tags_use_case,
    get_merge_tags_use_case,
    get_recolor_tag_use_case,
    get_rename_tag_use_case,
    get_tag_project_use_case,
    get_untag_project_use_case,
)
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryProjectRepository,
    InMemoryProjectTagRepository,
    InMemoryTagRepository,
    InMemoryUserRepository,
)

API = get_settings().api_prefix


def a_user(user_id: int, role: Role) -> User:
    return User(
        id=user_id,
        entra_oid=f"oid-{user_id}",
        email=f"user{user_id}@waat.fr",
        display_name=f"User {user_id}",
        role=role,
    )


TEAMMATE = a_user(2, Role.TEAMMATE)
MANAGER = a_user(3, Role.MANAGER)


class FakeSession:
    """Only what the routes ask of a session: that it be committed."""

    async def commit(self) -> None:
        return None


def sign_in(user: User) -> AsyncClient:
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
    users = InMemoryUserRepository([TEAMMATE, MANAGER])
    tags = InMemoryTagRepository()
    links = InMemoryProjectTagRepository(tags)
    audit = InMemoryAuditLogRepository()

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = FakeSession
    app.dependency_overrides[get_tag_project_use_case] = lambda: TagProjectUseCase(
        users, projects, tags, links, audit
    )
    app.dependency_overrides[get_untag_project_use_case] = lambda: UntagProjectUseCase(
        users, projects, tags, links, audit
    )
    app.dependency_overrides[get_list_tags_use_case] = lambda: ListTagsUseCase(tags)
    app.dependency_overrides[get_rename_tag_use_case] = lambda: RenameTagUseCase(
        users, tags, links, audit
    )
    app.dependency_overrides[get_recolor_tag_use_case] = lambda: RecolorTagUseCase(
        users, tags, links, audit
    )
    app.dependency_overrides[get_merge_tags_use_case] = lambda: MergeTagsUseCase(
        users, tags, links, audit
    )
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture(autouse=True)
def _forget_the_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


async def tag(client: AsyncClient, name: str, project_id: int = 10) -> dict:
    response = await client.post(
        f"{API}/projects/{project_id}/tags", json={"name": name}
    )
    assert response.status_code == 200, response.text
    return response.json()


async def test_tagging_a_mission_answers_with_the_tag_and_its_color() -> None:
    client = sign_in(TEAMMATE)

    body = await tag(client, "Chronopost")

    assert body["name"] == "Chronopost"
    assert body["color"] == "red"
    assert isinstance(body["id"], int)


async def test_tagging_off_project_work_is_refused() -> None:
    client = sign_in(TEAMMATE)

    response = await client.post(f"{API}/projects/12/tags", json={"name": "Suez"})

    assert response.status_code == 422


async def test_tagging_with_a_blank_name_is_refused() -> None:
    client = sign_in(TEAMMATE)

    response = await client.post(f"{API}/projects/10/tags", json={"name": "   "})

    assert response.status_code == 422


async def test_tagging_an_unknown_mission_is_a_404() -> None:
    client = sign_in(TEAMMATE)

    response = await client.post(f"{API}/projects/404/tags", json={"name": "Suez"})

    assert response.status_code == 404


async def test_taking_a_tag_off_answers_with_no_content() -> None:
    client = sign_in(TEAMMATE)
    suez = await tag(client, "Suez")

    response = await client.delete(f"{API}/projects/10/tags/{suez['id']}")

    assert response.status_code == 204


async def test_taking_off_an_unknown_tag_is_a_404() -> None:
    client = sign_in(TEAMMATE)

    assert (await client.delete(f"{API}/projects/10/tags/404")).status_code == 404


async def test_the_list_gives_the_tags_in_use_with_their_count() -> None:
    client = sign_in(TEAMMATE)
    await tag(client, "Suez")

    response = await client.get(f"{API}/tags")

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "Suez", "color": "red", "project_count": 1}
    ]


async def test_the_list_narrows_to_what_was_typed() -> None:
    client = sign_in(TEAMMATE)
    await tag(client, "Suez")
    await tag(client, "Frigo")

    response = await client.get(f"{API}/tags", params={"search": "sue"})

    assert [t["name"] for t in response.json()] == ["Suez"]


async def test_a_teammate_may_not_rename_a_tag() -> None:
    client = sign_in(TEAMMATE)
    suez = await tag(client, "Suez")

    response = await client.post(
        f"{API}/tags/{suez['id']}/rename", json={"name": "Suez Group"}
    )

    assert response.status_code == 403


async def test_a_manager_renames_a_tag() -> None:
    client = sign_in(MANAGER)
    suez = await tag(client, "Suez")

    response = await client.post(
        f"{API}/tags/{suez['id']}/rename", json={"name": "Suez Group"}
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Suez Group"


async def test_renaming_into_the_name_of_another_tag_is_a_409() -> None:
    client = sign_in(MANAGER)
    await tag(client, "Suez")
    other = await tag(client, "Suez Env")

    response = await client.post(
        f"{API}/tags/{other['id']}/rename", json={"name": "suez"}
    )

    assert response.status_code == 409


async def test_a_manager_recolors_a_tag() -> None:
    client = sign_in(MANAGER)
    suez = await tag(client, "Suez")

    response = await client.post(
        f"{API}/tags/{suez['id']}/recolor", json={"color": "violet"}
    )

    assert response.status_code == 200
    assert response.json()["color"] == "violet"


async def test_a_color_outside_the_palette_is_refused() -> None:
    client = sign_in(MANAGER)
    suez = await tag(client, "Suez")

    response = await client.post(
        f"{API}/tags/{suez['id']}/recolor", json={"color": "#ff00ff"}
    )

    assert response.status_code == 422


async def test_a_teammate_may_not_recolor_a_tag() -> None:
    client = sign_in(TEAMMATE)
    suez = await tag(client, "Suez")

    response = await client.post(
        f"{API}/tags/{suez['id']}/recolor", json={"color": "violet"}
    )

    assert response.status_code == 403


async def test_a_manager_folds_a_tag_into_another() -> None:
    client = sign_in(MANAGER)
    suez = await tag(client, "Suez")
    duplicate = await tag(client, "Suez Env")

    response = await client.post(
        f"{API}/tags/{duplicate['id']}/merge", json={"target_id": suez["id"]}
    )

    assert response.status_code == 200
    assert response.json()["id"] == suez["id"]
    listed = (await client.get(f"{API}/tags")).json()
    assert [t["name"] for t in listed] == ["Suez"]


async def test_a_teammate_may_not_merge_tags() -> None:
    client = sign_in(TEAMMATE)
    suez = await tag(client, "Suez")
    duplicate = await tag(client, "Suez Env")

    response = await client.post(
        f"{API}/tags/{duplicate['id']}/merge", json={"target_id": suez["id"]}
    )

    assert response.status_code == 403
