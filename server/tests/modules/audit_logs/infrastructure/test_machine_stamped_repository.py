"""What a line of the log says when a machine wrote it.

`actor_id` is a foreign key to `users`, and for a machine that human is the
key's owner — the one who answers for it. That alone would make a machine's
line indistinguishable from the owner's own, so the key is named beside it.
"""

from datetime import UTC, datetime

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.infrastructure.machine_stamped_repository import (
    MachineStampedAuditLog,
)
from src.shared.utils import clock
from tests.helpers.in_memory_repositories import InMemoryAuditLogRepository

KEY = "jns_ab12cd34ef56"


def a_log(payload: dict[str, object] | None = None) -> AuditLog:
    return AuditLog(
        action=AuditAction.PROJECT_UPDATE,
        actor_id=7,
        project_id=3,
        payload=payload,
    )


@pytest.mark.asyncio
async def test_a_line_written_by_a_machine_names_the_key() -> None:
    inner = InMemoryAuditLogRepository()

    await MachineStampedAuditLog(inner, KEY).add(a_log())

    assert inner.logs[0].payload == {"api_key": KEY}


@pytest.mark.asyncio
async def test_the_owner_stays_the_actor() -> None:
    # The trace says both what did it and who answers for it. Replacing the
    # actor would lose the second, which is the half a human can be asked about.
    inner = InMemoryAuditLogRepository()

    await MachineStampedAuditLog(inner, KEY).add(a_log())

    assert inner.logs[0].actor_id == 7


@pytest.mark.asyncio
async def test_what_the_use_case_already_wrote_is_kept() -> None:
    inner = InMemoryAuditLogRepository()

    await MachineStampedAuditLog(inner, KEY).add(a_log({"field": "label"}))

    assert inner.logs[0].payload == {"field": "label", "api_key": KEY}


@pytest.mark.asyncio
async def test_the_key_wins_over_a_name_the_payload_carried() -> None:
    # What called is a fact of the request, not of the use case.
    inner = InMemoryAuditLogRepository()

    await MachineStampedAuditLog(inner, KEY).add(a_log({"api_key": "jns_someoneelse"}))

    assert inner.logs[0].payload == {"api_key": KEY}


@pytest.mark.asyncio
async def test_reading_the_log_back_is_untouched() -> None:
    # Only writes are stamped. Reading is the same job whoever asks, and a
    # decorator that also filtered would answer a question nobody put.
    inner = InMemoryAuditLogRepository()
    stamped = MachineStampedAuditLog(inner, KEY)
    await stamped.add(a_log())

    assert len(await stamped.list_for_project(3, limit=10, offset=0)) == 1
    assert await stamped.count_for_project(3) == 1
    assert await stamped.count_all() == 1
    assert await stamped.list_for_user_month(7, clock.today(), 10, 0) == []
    assert await stamped.count_for_user_month(7, clock.today()) == 0
    assert await stamped.count_all(since=datetime(2099, 1, 1, tzinfo=UTC)) == 0
