"""Dropping a file on a mission, reading it back, taking it away — over HTTP."""

from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.core.database import get_db
from src.main import app
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.projects.application.use_cases.project_attachments import (
    DownloadProjectAttachmentUseCase,
    ListProjectAttachmentsUseCase,
    RemoveProjectAttachmentUseCase,
    UploadProjectAttachmentUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.presentation.dependencies import (
    get_download_attachment_use_case,
    get_list_attachments_use_case,
    get_remove_attachment_use_case,
    get_upload_attachment_use_case,
)
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryAttachmentStore,
    InMemoryAuditLogRepository,
    InMemoryProjectAttachmentRepository,
    InMemoryProjectRepository,
    InMemoryProjectUpdateRepository,
    InMemoryUserRepository,
)

ALICE = User(
    id=1,
    entra_oid="oid-1",
    email="alice@waat.fr",
    display_name="Alice Chen",
    role=Role.TEAMMATE,
)

URL = f"{get_settings().api_prefix}/projects"
WHEN = datetime(2026, 5, 20, 11, 35, tzinfo=UTC)


class FakeSession:
    """Only what the routes ask of a session: that it be committed."""

    async def commit(self) -> None:
        return None


def sign_in() -> tuple[
    AsyncClient,
    InMemoryProjectAttachmentRepository,
    InMemoryAttachmentStore,
    InMemoryProjectUpdateRepository,
]:
    files = InMemoryProjectAttachmentRepository()
    store = InMemoryAttachmentStore()
    updates = InMemoryProjectUpdateRepository()
    users = InMemoryUserRepository([ALICE])
    projects = InMemoryProjectRepository(
        [
            Project(
                id=10,
                label="Portail",
                kind=ProjectKind.PROJECT,
                status=ProjectStatus.DEVELOPMENT,
            )
        ]
    )
    kept = {
        "attachments": files,
        "store": store,
        "audit_logs": InMemoryAuditLogRepository(),
    }

    app.dependency_overrides[get_current_user] = lambda: ALICE
    app.dependency_overrides[get_db] = FakeSession
    app.dependency_overrides[get_upload_attachment_use_case] = (
        lambda: UploadProjectAttachmentUseCase(users=users, projects=projects, **kept)
    )
    app.dependency_overrides[get_remove_attachment_use_case] = (
        lambda: RemoveProjectAttachmentUseCase(**kept)
    )
    app.dependency_overrides[get_list_attachments_use_case] = (
        lambda: ListProjectAttachmentsUseCase(
            attachments=files, updates=updates, users=users
        )
    )
    app.dependency_overrides[get_download_attachment_use_case] = (
        lambda: DownloadProjectAttachmentUseCase(attachments=files, store=store)
    )
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    return client, files, store, updates


@pytest.fixture(autouse=True)
def _forget_the_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


async def _drop(
    client: AsyncClient, name: str = "capture.png", kind: str = "image/png"
) -> dict:
    response = await client.post(
        f"{URL}/10/attachments", files={"file": (name, b"\x89PNG-bytes", kind)}
    )
    assert response.status_code == 201, response.text
    body: dict = response.json()
    return body


async def test_a_file_dropped_comes_back_described() -> None:
    client, _, store, _ = sign_in()

    body = await _drop(client)

    assert body["filename"] == "capture.png"
    assert body["content_type"] == "image/png"
    assert body["size_bytes"] == len(b"\x89PNG-bytes")
    assert body["is_image"] is True
    assert body["uploader_name"] == "Alice Chen"
    assert body["used_in_updates"] == 0
    assert len(store.content) == 1


async def test_the_key_never_reaches_the_screen() -> None:
    """Where the bytes sit is nobody's business but the server's."""
    client, _, _, _ = sign_in()

    assert "storage_key" not in await _drop(client)


async def test_a_file_too_heavy_is_refused_with_a_readable_reason() -> None:
    client, _, store, _ = sign_in()

    response = await client.post(
        f"{URL}/10/attachments",
        files={"file": ("gros.bin", b"x" * (10 * 1024 * 1024 + 1), "application/zip")},
    )

    assert response.status_code == 422
    assert "10 Mo" in response.json()["detail"]
    assert store.content == {}


async def test_a_file_dropped_on_a_mission_that_does_not_exist_is_refused() -> None:
    client, _, _, _ = sign_in()

    response = await client.post(
        f"{URL}/999/attachments", files={"file": ("a.png", b"bytes", "image/png")}
    )

    assert response.status_code == 404


async def test_the_list_holds_what_was_dropped() -> None:
    client, _, _, _ = sign_in()
    await _drop(client, "note.pdf", "application/pdf")

    response = await client.get(f"{URL}/10/attachments")

    assert response.status_code == 200
    [one] = response.json()
    assert one["filename"] == "note.pdf"
    assert one["is_image"] is False


async def test_an_image_is_served_to_be_shown() -> None:
    client, _, _, _ = sign_in()
    dropped = await _drop(client)

    response = await client.get(f"{URL}/10/attachments/{dropped['id']}/content")

    assert response.status_code == 200
    assert response.content == b"\x89PNG-bytes"
    assert response.headers["content-type"] == "image/png"
    assert response.headers["content-disposition"].startswith("inline")
    assert response.headers["x-content-type-options"] == "nosniff"


async def test_a_page_dropped_as_a_file_is_never_served_to_be_shown() -> None:
    """Served inline from our own domain, it would run in the reader's browser."""
    client, _, _, _ = sign_in()
    dropped = await _drop(client, "piege.html", "text/html")

    response = await client.get(f"{URL}/10/attachments/{dropped['id']}/content")

    assert response.headers["content-disposition"].startswith("attachment")


async def test_asking_for_the_download_forces_the_save_dialog() -> None:
    client, _, _, _ = sign_in()
    dropped = await _drop(client)

    response = await client.get(
        f"{URL}/10/attachments/{dropped['id']}/content", params={"download": True}
    )

    assert response.headers["content-disposition"].startswith("attachment")
    assert "capture.png" in response.headers["content-disposition"]


async def test_a_name_with_an_accent_survives_the_journey() -> None:
    """A header is latin-1: a raw « é » there is a 500, not a download."""
    client, _, _, _ = sign_in()
    dropped = await _drop(client, "cahier de recette é.pdf", "application/pdf")

    response = await client.get(
        f"{URL}/10/attachments/{dropped['id']}/content", params={"download": True}
    )

    assert response.status_code == 200
    assert "filename*=utf-8''" in response.headers["content-disposition"]


async def test_a_file_nobody_ever_dropped_is_not_found() -> None:
    client, _, _, _ = sign_in()

    assert (await client.get(f"{URL}/10/attachments/404/content")).status_code == 404


async def test_withdrawing_a_file_leaves_nothing() -> None:
    client, files, store, _ = sign_in()
    dropped = await _drop(client)

    response = await client.delete(f"{URL}/10/attachments/{dropped['id']}")

    assert response.status_code == 204
    assert files.attachments == []
    assert store.content == {}


async def test_withdrawing_a_file_already_gone_is_not_found() -> None:
    client, _, _, _ = sign_in()

    assert (await client.delete(f"{URL}/10/attachments/404")).status_code == 404


async def test_a_file_is_not_served_under_another_mission() -> None:
    """The address names a mission, and the server holds it to that."""
    client, _, _, _ = sign_in()
    dropped = await _drop(client)

    answer = await client.get(f"{URL}/11/attachments/{dropped['id']}/content")

    assert answer.status_code == 404


async def test_a_file_is_not_withdrawn_under_another_mission() -> None:
    client, files, _, _ = sign_in()
    dropped = await _drop(client)

    answer = await client.delete(f"{URL}/11/attachments/{dropped['id']}")

    assert answer.status_code == 404
    assert len(files.attachments) == 1
