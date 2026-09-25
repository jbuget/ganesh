"""Deleting a mission from the reference list."""

from datetime import UTC, date, datetime

import pytest

from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.projects.application.dtos.project_dto import DeleteProjectCommand
from src.modules.projects.application.use_cases.delete_project import (
    DeleteProjectUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_attachment import ProjectAttachment
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.projects.domain.entities.service_registry import (
    Criticality,
    ServiceType,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)
from tests.helpers.in_memory_repositories import (
    InMemoryAttachmentStore,
    InMemoryAuditLogRepository,
    InMemoryEntryRepository,
    InMemoryNotificationRepository,
    InMemoryProjectAssigneeRepository,
    InMemoryProjectAttachmentRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
)

TEAMMATE = User(
    id=1,
    entra_oid="oid",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)


def project(id_: int = 10, kind: ProjectKind = ProjectKind.PROJECT) -> Project:
    return Project(
        id=id_,
        label=f"Mission {id_}",
        kind=kind,
        status=ProjectStatus.SCOPING,
        parent_id=10 if kind is ProjectKind.WORK_PACKAGE else None,
    )


def published(id_: int = 10) -> Project:
    """A mission the catalogue draws a card for, at a public address."""
    return Project(
        id=id_,
        label=f"Mission {id_}",
        kind=ProjectKind.PROJECT,
        status=ProjectStatus.SCOPING,
        is_published=True,
        slug=f"mission-{id_}",
        summary="Ce que le service rend.",
        criticality=Criticality.STANDARD,
        service_type=ServiceType.FULLSTACK,
    )


def entry(project_id: int) -> Entry:
    return Entry(
        id=None,
        user_id=1,
        project_id=project_id,
        activity_id=None,
        day=date(2026, 9, 15),
        value=DayValue(1.0),
        status_at_entry=ProjectStatus.SCOPING,
    )


def attachment(project_id: int, key: str) -> ProjectAttachment:
    return ProjectAttachment(
        id=None,
        project_id=project_id,
        uploaded_by=1,
        filename="capture.png",
        content_type="image/png",
        size_bytes=12,
        storage_key=key,
        uploaded_at=datetime(2026, 9, 15, 10, 0, tzinfo=UTC),
    )


def build(
    projects: list[Project] | None = None,
    entries: list[Entry] | None = None,
    attachments: list[ProjectAttachment] | None = None,
):
    repo = InMemoryProjectRepository(projects if projects is not None else [project()])
    audit = InMemoryAuditLogRepository()
    inbox = InMemoryNotificationRepository()
    files = InMemoryProjectAttachmentRepository()
    store = InMemoryAttachmentStore()
    for number, one in enumerate(attachments or [], start=1):
        one.id = number
        files.attachments.append(one)
        store.content[one.storage_key] = b"bytes"
    use_case = DeleteProjectUseCase(
        users=InMemoryUserRepository([TEAMMATE]),
        projects=repo,
        entries=InMemoryEntryRepository(entries or []),
        audit_logs=audit,
        assignees=InMemoryProjectAssigneeRepository({(10, ProjectRole.LEAD): [2]}),
        notifications=NotificationDelivery(inbox),
        attachments=files,
        store=store,
    )
    return use_case, repo, audit, inbox, store


async def test_a_mission_never_used_is_deleted() -> None:
    use_case, repo, _, _, _ = build()

    await use_case.execute(DeleteProjectCommand(actor_id=1, project_id=10))

    assert await repo.get_by_id(10) is None


async def test_a_mission_carrying_time_is_refused() -> None:
    use_case, repo, _, _, _ = build(entries=[entry(10)])

    with pytest.raises(ForbiddenActionError, match="archive"):
        await use_case.execute(DeleteProjectCommand(actor_id=1, project_id=10))

    assert await repo.get_by_id(10) is not None


async def test_a_project_carrying_sub_projects_is_refused() -> None:
    use_case, repo, _, _, _ = build([project(), project(11, ProjectKind.WORK_PACKAGE)])

    with pytest.raises(ForbiddenActionError, match="sub-project"):
        await use_case.execute(DeleteProjectCommand(actor_id=1, project_id=10))

    assert await repo.get_by_id(10) is not None


async def test_a_sub_project_never_used_is_deleted() -> None:
    use_case, repo, _, _, _ = build([project(), project(11, ProjectKind.WORK_PACKAGE)])

    await use_case.execute(DeleteProjectCommand(actor_id=1, project_id=11))

    assert await repo.get_by_id(11) is None


async def test_time_on_another_mission_does_not_block() -> None:
    """The count must cover the mission aimed at, not the whole reference list."""
    use_case, repo, _, _, _ = build([project(), project(11)], entries=[entry(11)])

    await use_case.execute(DeleteProjectCommand(actor_id=1, project_id=10))

    assert await repo.get_by_id(10) is None


async def test_a_published_mission_is_refused() -> None:
    """Its card would leave waat.tools without anybody deciding it."""
    use_case, repo, _, _, _ = build([published()])

    with pytest.raises(ForbiddenActionError, match="unpublish"):
        await use_case.execute(DeleteProjectCommand(actor_id=1, project_id=10))

    assert await repo.get_by_id(10) is not None


async def test_an_unknown_mission_is_rejected() -> None:
    use_case, _, _, _, _ = build()

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(DeleteProjectCommand(actor_id=1, project_id=999))


async def test_the_deletion_is_traced() -> None:
    use_case, _, audit, _, _ = build()

    await use_case.execute(DeleteProjectCommand(actor_id=1, project_id=10))

    log = audit.logs[-1]
    assert log.action.value == "project.delete"
    assert log.old_value == "Mission 10"


async def test_a_project_whose_work_package_carries_time_is_refused() -> None:
    """The project itself declared nothing; what it cuts into did.

    Deleting it would orphan the package, and with it the time declared on the
    package — the project's own empty count says nothing about that.
    """
    use_case, repo, _, _, _ = build(
        [project(), project(11, ProjectKind.WORK_PACKAGE)], entries=[entry(11)]
    )

    with pytest.raises(ForbiddenActionError):
        await use_case.execute(DeleteProjectCommand(actor_id=1, project_id=10))

    assert await repo.get_by_id(10) is not None


async def test_deleting_tells_everyone_who_was_on_the_mission() -> None:
    use_case, _, _, inbox, _ = build()

    await use_case.execute(DeleteProjectCommand(actor_id=1, project_id=10))

    [told] = inbox.notifications
    assert told.recipient_id == 2
    assert told.kind is NotificationKind.PROJECT_DELETED
    # Nothing left to read the name from: it travels with the line.
    assert told.project_id is None
    assert told.payload == {"project_label": "Mission 10"}


async def test_deleting_a_mission_takes_its_files_with_it() -> None:
    """The cascade drops the rows; nothing but this drops the bytes."""
    use_case, _, _, _, store = build(attachments=[attachment(10, "projects/10/a.png")])

    await use_case.execute(DeleteProjectCommand(actor_id=1, project_id=10))

    assert store.content == {}


async def test_deleting_a_mission_leaves_another_mission_its_files() -> None:
    use_case, _, _, _, store = build(
        [project(), project(11)],
        attachments=[attachment(11, "projects/11/b.png")],
    )

    await use_case.execute(DeleteProjectCommand(actor_id=1, project_id=10))

    assert "projects/11/b.png" in store.content


async def test_a_deletion_the_domain_refuses_keeps_the_files() -> None:
    use_case, _, _, _, store = build(
        entries=[entry(10)], attachments=[attachment(10, "projects/10/a.png")]
    )

    with pytest.raises(ForbiddenActionError):
        await use_case.execute(DeleteProjectCommand(actor_id=1, project_id=10))

    assert "projects/10/a.png" in store.content
