"""Which projects the register saw move, and in what order."""

from datetime import UTC, datetime, timedelta

import pytest

from src.modules.audit_logs.application.use_cases.list_touched_projects import (
    ListTouchedProjectsUseCase,
)
from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from tests.helpers.in_memory_repositories import InMemoryAuditLogRepository

NOON = datetime(2026, 9, 21, 12, 0, tzinfo=UTC)


def line(action: AuditAction, project_id: int, minutes: int) -> AuditLog:
    return AuditLog(
        action=action,
        actor_id=1,
        project_id=project_id,
        at=NOON + timedelta(minutes=minutes),
    )


@pytest.mark.asyncio
async def test_lists_the_projects_that_moved_freshest_first() -> None:
    audit_logs = InMemoryAuditLogRepository()
    await audit_logs.add(
        line(AuditAction.PROJECT_STATUS_CHANGE, project_id=1, minutes=0)
    )
    await audit_logs.add(line(AuditAction.PROJECT_UPDATE, project_id=2, minutes=10))

    touched = await ListTouchedProjectsUseCase(audit_logs).execute(limit=5)

    assert [one.project_id for one in touched] == [2, 1]
    assert touched[0].action == AuditAction.PROJECT_UPDATE
    assert touched[0].at == NOON + timedelta(minutes=10)


@pytest.mark.asyncio
async def test_names_a_project_once_however_often_it_moved() -> None:
    audit_logs = InMemoryAuditLogRepository()
    await audit_logs.add(
        line(AuditAction.PROJECT_STATUS_CHANGE, project_id=1, minutes=0)
    )
    await audit_logs.add(
        line(AuditAction.PROJECT_STATUS_CHANGE, project_id=1, minutes=5)
    )
    await audit_logs.add(line(AuditAction.PROJECT_UPDATE, project_id=2, minutes=1))

    touched = await ListTouchedProjectsUseCase(audit_logs).execute(limit=5)

    assert [one.project_id for one in touched] == [1, 2]
    # The last of them, not the first: what one wants to know is when it last
    # moved.
    assert touched[0].at == NOON + timedelta(minutes=5)


@pytest.mark.asyncio
async def test_declared_time_does_not_make_a_project_move() -> None:
    audit_logs = InMemoryAuditLogRepository()
    await audit_logs.add(line(AuditAction.ENTRY_SET, project_id=1, minutes=30))
    await audit_logs.add(
        line(AuditAction.PROJECT_STATUS_CHANGE, project_id=2, minutes=0)
    )

    touched = await ListTouchedProjectsUseCase(audit_logs).execute(limit=5)

    assert [one.project_id for one in touched] == [2]


@pytest.mark.asyncio
async def test_holds_to_the_number_asked_for() -> None:
    audit_logs = InMemoryAuditLogRepository()
    for project_id in range(1, 8):
        await audit_logs.add(
            line(AuditAction.PROJECT_UPDATE, project_id=project_id, minutes=project_id)
        )

    touched = await ListTouchedProjectsUseCase(audit_logs).execute(limit=3)

    assert [one.project_id for one in touched] == [7, 6, 5]


@pytest.mark.asyncio
async def test_a_gesture_naming_no_project_is_not_one() -> None:
    audit_logs = InMemoryAuditLogRepository()
    await audit_logs.add(AuditLog(action=AuditAction.USER_CREATE, actor_id=1, at=NOON))

    assert await ListTouchedProjectsUseCase(audit_logs).execute(limit=5) == []
