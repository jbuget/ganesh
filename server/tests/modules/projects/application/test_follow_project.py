"""Marking a mission as one the team keeps an eye on, and lowering the mark."""

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.projects.application.dtos.project_dto import FollowProjectCommand
from src.modules.projects.application.use_cases.follow_project import (
    FollowProjectUseCase,
    UnfollowProjectUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import EntityNotFoundError, ValidationError
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
PORTAL = 10
EDIT_LOT = 11
ABSENCES = 12


def reference_list() -> list[Project]:
    return [
        Project(
            id=PORTAL,
            label="Portail",
            kind=ProjectKind.PROJECT,
            status=ProjectStatus.DEVELOPMENT,
        ),
        Project(
            id=EDIT_LOT,
            label="Lot 2",
            kind=ProjectKind.WORK_PACKAGE,
            status=ProjectStatus.DEVELOPMENT,
            parent_id=PORTAL,
        ),
        Project(
            id=ABSENCES, label="Absences", kind=ProjectKind.OFF_PROJECT, status=None
        ),
    ]


def build():
    projects = InMemoryProjectRepository(reference_list())
    audit = InMemoryAuditLogRepository()
    users = InMemoryUserRepository([NINO])
    return (
        FollowProjectUseCase(users=users, projects=projects, audit_logs=audit),
        UnfollowProjectUseCase(users=users, projects=projects, audit_logs=audit),
        projects,
        audit,
    )


def gesture(project_id: int = PORTAL) -> FollowProjectCommand:
    return FollowProjectCommand(actor_id=2, project_id=project_id)


@pytest.mark.asyncio
async def test_following_marks_the_mission_and_is_traced() -> None:
    follow, _, projects, audit = build()

    await follow.execute(gesture())

    followed = await projects.get_by_id(PORTAL)
    assert followed is not None and followed.is_followed is True
    [line] = audit.logs
    assert line.action == AuditAction.PROJECT_FOLLOW
    assert line.actor_id == 2
    assert line.project_id == PORTAL


@pytest.mark.asyncio
async def test_a_work_package_is_followed_without_its_project() -> None:
    follow, _, projects, _ = build()

    await follow.execute(gesture(EDIT_LOT))

    package = await projects.get_by_id(EDIT_LOT)
    project = await projects.get_by_id(PORTAL)
    assert package is not None and package.is_followed is True
    assert project is not None and project.is_followed is False


@pytest.mark.asyncio
async def test_following_twice_writes_one_line() -> None:
    """A double click is not two gestures: the log says what changed."""
    follow, _, _, audit = build()

    await follow.execute(gesture())
    await follow.execute(gesture())

    assert len(audit.logs) == 1


@pytest.mark.asyncio
async def test_unfollowing_lowers_the_mark_and_is_traced() -> None:
    follow, unfollow, projects, audit = build()
    await follow.execute(gesture())

    await unfollow.execute(gesture())

    lowered = await projects.get_by_id(PORTAL)
    assert lowered is not None and lowered.is_followed is False
    assert [line.action for line in audit.logs] == [
        AuditAction.PROJECT_FOLLOW,
        AuditAction.PROJECT_UNFOLLOW,
    ]


@pytest.mark.asyncio
async def test_unfollowing_what_was_never_followed_writes_nothing() -> None:
    _, unfollow, _, audit = build()

    await unfollow.execute(gesture())

    assert audit.logs == []


@pytest.mark.asyncio
async def test_off_project_work_cannot_be_followed() -> None:
    follow, _, _, audit = build()

    with pytest.raises(ValidationError):
        await follow.execute(gesture(ABSENCES))
    assert audit.logs == []


@pytest.mark.asyncio
async def test_an_unknown_mission_is_refused() -> None:
    follow, _, _, _ = build()

    with pytest.raises(EntityNotFoundError):
        await follow.execute(gesture(404))
