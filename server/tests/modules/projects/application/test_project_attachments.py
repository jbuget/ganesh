"""Dropping a file on a mission, reading it back, taking it away."""

from datetime import UTC, datetime

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.projects.application.dtos.attachment_dto import (
    RemoveAttachmentCommand,
    UploadAttachmentCommand,
)
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
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import EntityNotFoundError, ValidationError
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
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)
NINO = User(
    id=2,
    entra_oid="oid-2",
    email="n.garo.ext@waat.fr",
    display_name="N. Garo",
    role=Role.TEAMMATE,
)
WHEN = datetime(2026, 5, 20, 11, 35, tzinfo=UTC)


def build():
    attachments = InMemoryProjectAttachmentRepository()
    store = InMemoryAttachmentStore()
    audit = InMemoryAuditLogRepository()
    updates = InMemoryProjectUpdateRepository()
    deps = {
        "users": InMemoryUserRepository([ALICE, NINO]),
        "projects": InMemoryProjectRepository(
            [
                Project(
                    id=10,
                    label="Portail",
                    kind=ProjectKind.PROJECT,
                    status=ProjectStatus.DEVELOPMENT,
                )
            ]
        ),
        "attachments": attachments,
        "store": store,
        "audit_logs": audit,
    }
    return (
        UploadProjectAttachmentUseCase(**deps),
        ListProjectAttachmentsUseCase(
            attachments=attachments,
            updates=updates,
            users=InMemoryUserRepository([ALICE, NINO]),
        ),
        DownloadProjectAttachmentUseCase(attachments=attachments, store=store),
        RemoveProjectAttachmentUseCase(**deps),
        {
            "attachments": attachments,
            "store": store,
            "audit": audit,
            "updates": updates,
        },
    )


def a_drop(**changes: object) -> UploadAttachmentCommand:
    fields: dict[str, object] = {
        "actor_id": 1,
        "project_id": 10,
        "filename": "capture.png",
        "content_type": "image/png",
        "content": b"\x89PNG-and-the-rest",
    }
    fields.update(changes)
    return UploadAttachmentCommand(**fields)  # type: ignore[arg-type]


async def test_dropping_a_file_puts_the_bytes_down_and_writes_the_line() -> None:
    upload, _, _, _, kept = build()

    attachment = await upload.execute(a_drop(), now=WHEN)

    assert attachment.id == 1
    assert attachment.filename == "capture.png"
    assert attachment.size_bytes == len(b"\x89PNG-and-the-rest")
    assert kept["store"].content[attachment.storage_key] == b"\x89PNG-and-the-rest"


async def test_the_key_is_drawn_and_never_taken_from_the_name() -> None:
    upload, _, _, _, _ = build()

    attachment = await upload.execute(a_drop(filename="capture.png"), now=WHEN)

    assert attachment.storage_key.startswith("projects/10/")
    assert "capture" not in attachment.storage_key


async def test_dropping_a_file_is_traced_against_the_mission() -> None:
    upload, _, _, _, kept = build()

    await upload.execute(a_drop(), now=WHEN)

    line = kept["audit"].logs[-1]
    assert line.action == AuditAction.ATTACHMENT_ADD
    assert line.actor_id == 1
    assert line.project_id == 10
    # The Journal reads the name from the line: the file may be gone by then.
    assert line.new_value == "capture.png"
    assert line.payload["attachment_id"] == 1


async def test_a_file_too_heavy_never_reaches_the_store() -> None:
    upload, _, _, _, kept = build()

    with pytest.raises(ValidationError):
        await upload.execute(a_drop(content=b"x" * (10 * 1024 * 1024 + 1)), now=WHEN)

    assert kept["store"].content == {}
    assert kept["attachments"].attachments == []


async def test_a_file_dropped_on_a_mission_that_does_not_exist_is_refused() -> None:
    upload, _, _, _, _ = build()

    with pytest.raises(EntityNotFoundError):
        await upload.execute(a_drop(project_id=999), now=WHEN)


async def test_the_list_says_who_dropped_each_file_and_when() -> None:
    upload, listing, _, _, _ = build()
    await upload.execute(a_drop(actor_id=2, filename="note.pdf"), now=WHEN)

    signed = await listing.execute(10)

    assert [one.attachment.filename for one in signed] == ["note.pdf"]
    assert signed[0].uploader.display_name == "N. Garo"


async def test_the_list_says_how_many_updates_show_each_file() -> None:
    """A screen must be able to warn before a thread loses its picture."""
    upload, listing, _, _, kept = build()
    attachment = await upload.execute(a_drop(), now=WHEN)
    body = (
        f"Le bug : ![capture](/api/v1/projects/10/attachments/{attachment.id}/content)"
    )
    await kept["updates"].add(
        ProjectUpdate(id=None, project_id=10, author_id=1, body=body, published_at=WHEN)
    )

    signed = await listing.execute(10)

    assert signed[0].used_in_updates == 1


async def test_a_file_shown_nowhere_is_shown_nowhere() -> None:
    upload, listing, _, _, _ = build()
    await upload.execute(a_drop(), now=WHEN)

    assert (await listing.execute(10))[0].used_in_updates == 0


async def test_the_files_of_another_mission_are_not_listed() -> None:
    upload, listing, _, _, _ = build()
    await upload.execute(a_drop(), now=WHEN)

    assert await listing.execute(11) == []


async def test_downloading_hands_back_the_bytes_that_were_dropped() -> None:
    upload, _, download, _, _ = build()
    attachment = await upload.execute(a_drop(), now=WHEN)
    assert attachment.id is not None

    found, content = await download.execute(attachment.id)

    assert found.filename == "capture.png"
    assert content == b"\x89PNG-and-the-rest"


async def test_downloading_a_file_nobody_ever_dropped_is_refused() -> None:
    _, _, download, _, _ = build()

    with pytest.raises(EntityNotFoundError):
        await download.execute(404)


async def test_withdrawing_a_file_takes_the_line_and_the_bytes() -> None:
    upload, _, _, remove, kept = build()
    attachment = await upload.execute(a_drop(), now=WHEN)
    assert attachment.id is not None

    await remove.execute(
        RemoveAttachmentCommand(actor_id=2, attachment_id=attachment.id)
    )

    assert kept["attachments"].attachments == []
    assert kept["store"].content == {}


async def test_anybody_on_the_team_may_withdraw_a_file() -> None:
    """A file belongs to the mission, not to whoever happened to drop it."""
    upload, listing, _, remove, _ = build()
    attachment = await upload.execute(a_drop(actor_id=1), now=WHEN)
    assert attachment.id is not None

    await remove.execute(
        RemoveAttachmentCommand(actor_id=2, attachment_id=attachment.id)
    )

    assert await listing.execute(10) == []


async def test_withdrawing_a_file_is_traced_with_the_name_it_carried() -> None:
    upload, _, _, remove, kept = build()
    attachment = await upload.execute(a_drop(), now=WHEN)
    assert attachment.id is not None

    await remove.execute(
        RemoveAttachmentCommand(actor_id=2, attachment_id=attachment.id)
    )

    line = kept["audit"].logs[-1]
    assert line.action == AuditAction.ATTACHMENT_REMOVE
    assert line.actor_id == 2
    assert line.project_id == 10
    assert line.old_value == "capture.png"


async def test_withdrawing_a_file_that_is_already_gone_is_refused() -> None:
    _, _, _, remove, _ = build()

    with pytest.raises(EntityNotFoundError):
        await remove.execute(RemoveAttachmentCommand(actor_id=1, attachment_id=404))
