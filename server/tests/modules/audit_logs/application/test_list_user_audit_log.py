"""One teammate's audit log, read page by page."""

from datetime import date, datetime

import pytest

from src.modules.audit_logs.application.use_cases.list_user_audit_log import (
    ListUserAuditLogUseCase,
)
from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
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
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)
NINO = User(
    id=2,
    entra_oid="oid-2",
    email="n.garo.ext@waat.fr",
    display_name="N. Garo",
    role=Role.MANAGER,
)
WAATCHER = Project(
    id=10, label="WAATcher", kind=ProjectKind.PROJECT, status=ProjectStatus.DEVELOPMENT
)


def build(logs: list[AuditLog]) -> ListUserAuditLogUseCase:
    audit = InMemoryAuditLogRepository()
    audit.logs = logs
    for rank, log in enumerate(logs, start=1):
        log.id = rank
    return ListUserAuditLogUseCase(
        audit_logs=audit,
        users=InMemoryUserRepository([ALICE, NINO]),
        projects=InMemoryProjectRepository([WAATCHER]),
    )


def what_she_did(at: datetime, actor_id: int = 1) -> AuditLog:
    return AuditLog(
        action=AuditAction.PROJECT_UPDATE, actor_id=actor_id, project_id=10, at=at
    )


def what_was_done_to_her(at: datetime, target_user_id: int = 1) -> AuditLog:
    return AuditLog(
        action=AuditAction.USER_ROLE_CHANGE,
        actor_id=2,
        target_user_id=target_user_id,
        old_value="teammate",
        new_value="manager",
        at=at,
    )


@pytest.mark.asyncio
async def test_a_teammate_s_log_reads_the_most_recent_first() -> None:
    use_case = build(
        [
            what_she_did(datetime(2026, 9, 1, 9, 0)),
            what_she_did(datetime(2026, 9, 3, 9, 0)),
            what_she_did(datetime(2026, 9, 2, 9, 0)),
        ]
    )

    page = await use_case.execute(user_id=1, limit=50, offset=0)

    assert [entry.log.at.day for entry in page.entries] == [3, 2, 1]
    assert page.total == 3


@pytest.mark.asyncio
async def test_a_teammate_s_log_holds_both_sides_of_their_id() -> None:
    """What they did, and what was done to them: the panel answers both."""
    use_case = build(
        [
            what_she_did(datetime(2026, 9, 1, 9, 0)),
            what_was_done_to_her(datetime(2026, 9, 2, 9, 0)),
        ]
    )

    page = await use_case.execute(user_id=1, limit=50, offset=0)

    assert [entry.log.action for entry in page.entries] == [
        AuditAction.USER_ROLE_CHANGE,
        AuditAction.PROJECT_UPDATE,
    ]
    assert page.total == 2


@pytest.mark.asyncio
async def test_a_teammate_s_log_leaves_out_what_names_somebody_else() -> None:
    use_case = build(
        [
            what_she_did(datetime(2026, 9, 1, 9, 0), actor_id=2),
            what_was_done_to_her(datetime(2026, 9, 2, 9, 0), target_user_id=2),
        ]
    )

    page = await use_case.execute(user_id=1, limit=50, offset=0)

    assert page.entries == []
    assert page.total == 0


@pytest.mark.asyncio
async def test_a_teammate_s_log_serves_one_page_and_counts_the_whole() -> None:
    use_case = build(
        [what_she_did(datetime(2026, 9, day, 9, 0)) for day in range(1, 6)]
    )

    page = await use_case.execute(user_id=1, limit=2, offset=2)

    assert [entry.log.at.day for entry in page.entries] == [3, 2]
    assert page.total == 5


@pytest.mark.asyncio
async def test_a_teammate_s_log_names_the_mission_of_every_line() -> None:
    """The panel is a person, not a project: an unplaced gesture says nothing."""
    use_case = build(
        [
            AuditLog(
                action=AuditAction.ENTRY_SET,
                actor_id=2,
                target_user_id=1,
                project_id=10,
                day=date(2026, 9, 14),
                new_value="0.5",
                at=datetime(2026, 9, 14, 9, 0),
            )
        ]
    )

    entry = (await use_case.execute(user_id=1, limit=50, offset=0)).entries[0]

    assert entry.project is not None and entry.project.label == "WAATcher"
    assert entry.actor is not None and entry.actor.display_name == "N. Garo"
    assert entry.target_user is not None and entry.target_user.display_name == "L. Chen"
