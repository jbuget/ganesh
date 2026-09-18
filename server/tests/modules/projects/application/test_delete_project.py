"""Deleting a mission from the reference list."""

from datetime import date

import pytest

from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.projects.application.dtos.project_dto import DeleteProjectCommand
from src.modules.projects.application.use_cases.delete_project import (
    DeleteProjectUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryEntryRepository,
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


def entry(project_id: int) -> Entry:
    return Entry(
        id=None,
        user_id=1,
        project_id=project_id,
        day=date(2026, 9, 15),
        value=DayValue(1.0),
        status_at_entry=ProjectStatus.SCOPING,
    )


def build(projects: list[Project] | None = None, entries: list[Entry] | None = None):
    repo = InMemoryProjectRepository(projects if projects is not None else [project()])
    audit = InMemoryAuditLogRepository()
    use_case = DeleteProjectUseCase(
        users=InMemoryUserRepository([TEAMMATE]),
        projects=repo,
        entries=InMemoryEntryRepository(entries or []),
        audit_logs=audit,
    )
    return use_case, repo, audit


async def test_a_mission_never_used_is_deleted() -> None:
    use_case, repo, _ = build()

    await use_case.execute(DeleteProjectCommand(actor_id=1, project_id=10))

    assert await repo.get_by_id(10) is None


async def test_a_mission_carrying_time_is_refused() -> None:
    use_case, repo, _ = build(entries=[entry(10)])

    with pytest.raises(ForbiddenActionError, match="archive"):
        await use_case.execute(DeleteProjectCommand(actor_id=1, project_id=10))

    assert await repo.get_by_id(10) is not None


async def test_a_project_carrying_sub_projects_is_refused() -> None:
    use_case, repo, _ = build([project(), project(11, ProjectKind.WORK_PACKAGE)])

    with pytest.raises(ForbiddenActionError, match="sub-project"):
        await use_case.execute(DeleteProjectCommand(actor_id=1, project_id=10))

    assert await repo.get_by_id(10) is not None


async def test_a_sub_project_never_used_is_deleted() -> None:
    use_case, repo, _ = build([project(), project(11, ProjectKind.WORK_PACKAGE)])

    await use_case.execute(DeleteProjectCommand(actor_id=1, project_id=11))

    assert await repo.get_by_id(11) is None


async def test_time_on_another_mission_does_not_block() -> None:
    """The count must cover the mission aimed at, not the whole reference list."""
    use_case, repo, _ = build([project(), project(11)], entries=[entry(11)])

    await use_case.execute(DeleteProjectCommand(actor_id=1, project_id=10))

    assert await repo.get_by_id(10) is None


async def test_an_unknown_mission_is_rejected() -> None:
    use_case, _, _ = build()

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(DeleteProjectCommand(actor_id=1, project_id=999))


async def test_the_deletion_is_traced() -> None:
    use_case, _, audit = build()

    await use_case.execute(DeleteProjectCommand(actor_id=1, project_id=10))

    log = audit.logs[-1]
    assert log.action.value == "project.delete"
    assert log.old_value == "Mission 10"
