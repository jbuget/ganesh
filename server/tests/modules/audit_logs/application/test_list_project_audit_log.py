"""A mission's audit log, read page by page."""

from datetime import date, datetime

import pytest

from src.modules.audit_logs.application.use_cases.list_project_audit_log import (
    ListProjectAuditLogUseCase,
)
from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
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
    is_active=False,
)


def build(logs: list[AuditLog]) -> ListProjectAuditLogUseCase:
    audit = InMemoryAuditLogRepository()
    audit.logs = logs
    for rank, log in enumerate(logs, start=1):
        log.id = rank
    return ListProjectAuditLogUseCase(
        audit_logs=audit, users=InMemoryUserRepository([ALICE, NINO])
    )


def a_log(project_id: int, at: datetime, actor_id: int = 1) -> AuditLog:
    return AuditLog(
        action=AuditAction.PROJECT_UPDATE,
        actor_id=actor_id,
        project_id=project_id,
        at=at,
    )


@pytest.mark.asyncio
async def test_list_project_audit_log_reads_the_most_recent_first() -> None:
    use_case = build(
        [
            a_log(10, datetime(2026, 9, 1, 9, 0)),
            a_log(10, datetime(2026, 9, 3, 9, 0)),
            a_log(10, datetime(2026, 9, 2, 9, 0)),
        ]
    )

    page = await use_case.execute(project_id=10, limit=50, offset=0)

    assert [entry.log.at.day for entry in page.entries] == [3, 2, 1]
    assert page.total == 3


@pytest.mark.asyncio
async def test_list_project_audit_log_keeps_to_the_mission_asked_for() -> None:
    use_case = build(
        [a_log(10, datetime(2026, 9, 1, 9, 0)), a_log(11, datetime(2026, 9, 2, 9, 0))]
    )

    page = await use_case.execute(project_id=10, limit=50, offset=0)

    assert page.total == 1
    assert page.entries[0].log.project_id == 10


@pytest.mark.asyncio
async def test_list_project_audit_log_serves_one_page_and_counts_the_whole() -> None:
    use_case = build([a_log(10, datetime(2026, 9, day, 9, 0)) for day in range(1, 6)])

    page = await use_case.execute(project_id=10, limit=2, offset=2)

    assert [entry.log.at.day for entry in page.entries] == [3, 2]
    # The count is of the whole log, not of the page: it is what tells the
    # screen there is more to ask for.
    assert page.total == 5


@pytest.mark.asyncio
async def test_list_project_audit_log_signs_the_actor_and_whose_month_it_touched() -> (
    None
):
    use_case = build(
        [
            AuditLog(
                action=AuditAction.ENTRY_SET,
                actor_id=1,
                target_user_id=2,
                project_id=10,
                day=date(2026, 9, 14),
                new_value="0.5",
                at=datetime(2026, 9, 14, 9, 0),
            )
        ]
    )

    entry = (await use_case.execute(project_id=10, limit=50, offset=0)).entries[0]

    assert entry.actor is not None and entry.actor.display_name == "L. Chen"
    # Deactivated, N. Garo still signs what happened while they were there:
    # a log that forgets who it names stops being one.
    assert entry.target_user is not None and entry.target_user.display_name == "N. Garo"


@pytest.mark.asyncio
async def test_list_project_audit_log_survives_an_actor_that_is_gone() -> None:
    use_case = build([a_log(10, datetime(2026, 9, 1, 9, 0), actor_id=99)])

    entry = (await use_case.execute(project_id=10, limit=50, offset=0)).entries[0]

    assert entry.actor is None
