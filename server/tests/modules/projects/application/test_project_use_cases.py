"""Managing the mission reference list, open to the whole team."""

import pytest

from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.projects.application.dtos.project_dto import (
    ChangeProjectStatusCommand,
    CreateProjectCommand,
)
from src.modules.projects.application.use_cases.change_project_status import (
    ChangeProjectStatusUseCase,
)
from src.modules.projects.application.use_cases.create_project import (
    CreateProjectUseCase,
)
from src.modules.projects.application.use_cases.list_projects import ListProjectsUseCase
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import EntityNotFoundError, ValidationError
from tests.helpers.in_memory_repositories import (
    InMemoryActivityRepository,
    InMemoryAuditLogRepository,
    InMemoryEntryRepository,
    InMemoryNotificationRepository,
    InMemoryProjectAssigneeRepository,
    InMemoryProjectDetailRepository,
    InMemoryProjectRepository,
    InMemoryProjectUpdateRepository,
    InMemoryUserRepository,
)

TEAMMATE = User(
    id=1,
    entra_oid="oid",
    email="n.garo.ext@waat.fr",
    display_name="N. Garo",
    role=Role.TEAMMATE,
)


def make_portail() -> Project:
    """A fresh instance per test: entities are mutable."""
    return Project(
        id=10, label="Portail", kind=ProjectKind.PROJECT, status=ProjectStatus.SCOPING
    )


def build(projects: list[Project] | None = None):
    users = InMemoryUserRepository([TEAMMATE])
    repo = InMemoryProjectRepository(
        projects if projects is not None else [make_portail()]
    )
    audit = InMemoryAuditLogRepository()
    inbox = InMemoryNotificationRepository()
    return (
        CreateProjectUseCase(users=users, projects=repo, audit_logs=audit),
        ChangeProjectStatusUseCase(
            users=users,
            projects=repo,
            details=InMemoryProjectDetailRepository(),
            audit_logs=audit,
            assignees=InMemoryProjectAssigneeRepository({(10, ProjectRole.LEAD): [2]}),
            notifications=NotificationDelivery(inbox),
        ),
        ListProjectsUseCase(
            projects=repo,
            activities=InMemoryActivityRepository(),
            entries=InMemoryEntryRepository(),
            assignees=InMemoryProjectAssigneeRepository(),
            users=users,
            updates=InMemoryProjectUpdateRepository(),
            details=InMemoryProjectDetailRepository(),
        ),
        repo,
        audit,
        inbox,
    )


async def test_any_teammate_can_create_a_project() -> None:
    create, _, _, repo, _, _ = build(projects=[])

    project = await create.execute(
        CreateProjectCommand(
            actor_id=1,
            label="Nouveau portail",
            kind=ProjectKind.PROJECT,
            status=ProjectStatus.EXPLORATION,
        )
    )

    assert project.id is not None
    assert len(await repo.list_all()) == 1


async def test_a_new_project_is_not_linked_to_monday() -> None:
    """V1 is decoupled from Monday: the link comes later."""
    create, _, _, _, _, _ = build(projects=[])

    project = await create.execute(
        CreateProjectCommand(
            actor_id=1,
            label="Nouveau",
            kind=ProjectKind.PROJECT,
            status=ProjectStatus.EXPLORATION,
        )
    )

    assert project.monday_item_id is None
    assert project.is_syncable_to_monday is False


async def test_a_work_package_must_reference_an_existing_parent() -> None:
    create, _, _, _, _, _ = build()

    with pytest.raises(EntityNotFoundError):
        await create.execute(
            CreateProjectCommand(
                actor_id=1,
                label="Lot 1",
                kind=ProjectKind.WORK_PACKAGE,
                status=ProjectStatus.SCOPING,
                parent_id=999,
            )
        )


async def test_a_work_package_is_attached_to_its_parent() -> None:
    create, _, _, repo, _, _ = build()

    work_package = await create.execute(
        CreateProjectCommand(
            actor_id=1,
            label="Lot 1",
            kind=ProjectKind.WORK_PACKAGE,
            status=ProjectStatus.SCOPING,
            parent_id=10,
        )
    )

    assert work_package.parent_id == 10
    assert [p.id for p in await repo.list_children(10)] == [work_package.id]


async def test_a_work_package_cannot_be_attached_to_another_one() -> None:
    """The hierarchy stops at two levels."""
    parent = make_portail()
    work_package = Project(
        id=20,
        label="Lot existant",
        kind=ProjectKind.WORK_PACKAGE,
        status=ProjectStatus.SCOPING,
        parent_id=10,
    )
    create, _, _, _, _, _ = build(projects=[parent, work_package])

    with pytest.raises(ValidationError):
        await create.execute(
            CreateProjectCommand(
                actor_id=1,
                label="Sous-sous-projet",
                kind=ProjectKind.WORK_PACKAGE,
                status=ProjectStatus.SCOPING,
                parent_id=20,
            )
        )


async def test_a_work_package_cannot_hang_under_an_off_project_activity() -> None:
    activity = Project(
        id=30, label="Absences", kind=ProjectKind.OFF_PROJECT, status=None
    )
    create, _, _, _, _, _ = build(projects=[activity])

    with pytest.raises(ValidationError):
        await create.execute(
            CreateProjectCommand(
                actor_id=1,
                label="Lot",
                kind=ProjectKind.WORK_PACKAGE,
                status=ProjectStatus.SCOPING,
                parent_id=30,
            )
        )


async def test_an_off_project_activity_carries_no_status() -> None:
    create, _, _, _, _, _ = build(projects=[])

    activity = await create.execute(
        CreateProjectCommand(
            actor_id=1, label="Formation", kind=ProjectKind.OFF_PROJECT, status=None
        )
    )

    assert activity.status is None


async def test_a_blank_label_is_rejected() -> None:
    create, _, _, _, _, _ = build()

    with pytest.raises(ValidationError):
        await create.execute(
            CreateProjectCommand(
                actor_id=1,
                label="  ",
                kind=ProjectKind.PROJECT,
                status=ProjectStatus.SCOPING,
            )
        )


async def test_creation_is_traced() -> None:
    create, _, _, _, audit, _ = build(projects=[])

    await create.execute(
        CreateProjectCommand(
            actor_id=1,
            label="Nouveau",
            kind=ProjectKind.PROJECT,
            status=ProjectStatus.EXPLORATION,
        )
    )

    assert audit.logs[-1].action.value == "project.create"


async def test_anyone_can_change_a_project_status() -> None:
    _, change, _, repo, _, _ = build()

    await change.execute(
        ChangeProjectStatusCommand(
            actor_id=1, project_id=10, status=ProjectStatus.DEVELOPMENT
        )
    )

    project = await repo.get_by_id(10)
    assert project is not None
    assert project.status is ProjectStatus.DEVELOPMENT


async def test_a_status_change_records_the_transition() -> None:
    _, change, _, _, audit, _ = build()

    await change.execute(
        ChangeProjectStatusCommand(
            actor_id=1, project_id=10, status=ProjectStatus.DEVELOPMENT
        )
    )

    log = audit.logs[-1]
    assert log.action.value == "project.status_change"
    assert (log.old_value, log.new_value) == ("scoping", "development")


async def test_listing_returns_active_projects() -> None:
    _, _, list_projects, _, _, _ = build()

    missions = await list_projects.execute()
    assert len(missions) == 1
    assert missions[0].project.label == "Portail"


async def test_a_mission_never_used_is_reported_as_deletable() -> None:
    _, _, list_projects, _, _, _ = build()

    assert (await list_projects.execute())[0].is_deletable is True


async def test_a_created_work_package_comes_back_with_its_project_axis() -> None:
    """The screen that opens on it reads the axis the list already showed."""
    portail = make_portail()
    portail.category = ProjectCategory.INNOVATE
    create, _, _, _, _, _ = build([portail])

    created = await create.execute(
        CreateProjectCommand(
            actor_id=1,
            label="Lot API",
            kind=ProjectKind.WORK_PACKAGE,
            status=ProjectStatus.EXPLORATION,
            parent_id=10,
        )
    )

    assert created.category is ProjectCategory.INNOVATE


async def test_a_work_package_changing_phase_keeps_its_project_axis() -> None:
    portail = make_portail()
    portail.category = ProjectCategory.STRUCTURE
    package = Project(
        id=11,
        label="Lot API",
        kind=ProjectKind.WORK_PACKAGE,
        status=ProjectStatus.SCOPING,
        parent_id=10,
    )
    _, change_status, _, _, _, _ = build([portail, package])

    moved = await change_status.execute(
        ChangeProjectStatusCommand(
            actor_id=1, project_id=11, status=ProjectStatus.DEVELOPMENT
        )
    )

    assert moved.category is ProjectCategory.STRUCTURE


async def test_a_phase_change_reaches_everyone_on_the_mission() -> None:
    _, change, _, _, _, inbox = build()

    await change.execute(
        ChangeProjectStatusCommand(
            actor_id=1, project_id=10, status=ProjectStatus.DEVELOPMENT
        )
    )

    [told] = inbox.notifications
    assert told.recipient_id == 2
    assert told.kind is NotificationKind.PROJECT_STATUS_CHANGED
    assert told.project_id == 10
    # Both ends travel with the line: « a fait passer en Réalisation ».
    assert told.payload == {"from": "scoping", "to": "development"}
