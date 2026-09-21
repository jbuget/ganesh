"""One month of one person's register, read page by page."""

from datetime import date, datetime

import pytest

from src.modules.audit_logs.application.use_cases.list_month_audit_log import (
    ListMonthAuditLogUseCase,
)
from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.projects.domain.entities.project import Project, ProjectKind
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
)

SEPTEMBER = date(2026, 9, 1)

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

WAATCHER = Project(id=10, label="WAATcher", kind=ProjectKind.PROJECT)
NOMAD = Project(id=11, label="NOMAD", kind=ProjectKind.PROJECT, is_active=False)


def build(logs: list[AuditLog]) -> ListMonthAuditLogUseCase:
    audit = InMemoryAuditLogRepository()
    audit.logs = logs
    for rank, log in enumerate(logs, start=1):
        log.id = rank
    return ListMonthAuditLogUseCase(
        audit_logs=audit,
        users=InMemoryUserRepository([ALICE, NINO]),
        projects=InMemoryProjectRepository([WAATCHER, NOMAD]),
    )


def an_entry(
    day: date,
    at: datetime,
    target_user_id: int = 1,
    project_id: int | None = 10,
) -> AuditLog:
    return AuditLog(
        action=AuditAction.ENTRY_SET,
        actor_id=1,
        target_user_id=target_user_id,
        project_id=project_id,
        day=day,
        at=at,
    )


@pytest.mark.asyncio
async def test_list_month_audit_log_reads_the_most_recent_first() -> None:
    use_case = build(
        [
            an_entry(date(2026, 9, 3), datetime(2026, 9, 3, 9, 0)),
            an_entry(date(2026, 9, 1), datetime(2026, 9, 5, 9, 0)),
            an_entry(date(2026, 9, 2), datetime(2026, 9, 4, 9, 0)),
        ]
    )

    page = await use_case.execute(target_user_id=1, month=SEPTEMBER, limit=50, offset=0)

    assert [entry.log.at.day for entry in page.entries] == [5, 4, 3]
    assert page.total == 3


@pytest.mark.asyncio
async def test_list_month_audit_log_keeps_to_the_month_asked_for() -> None:
    use_case = build(
        [
            an_entry(date(2026, 9, 30), datetime(2026, 9, 30, 9, 0)),
            an_entry(date(2026, 8, 31), datetime(2026, 8, 31, 9, 0)),
            an_entry(date(2026, 10, 1), datetime(2026, 10, 1, 9, 0)),
        ]
    )

    page = await use_case.execute(target_user_id=1, month=SEPTEMBER, limit=50, offset=0)

    assert page.total == 1
    assert page.entries[0].log.day == date(2026, 9, 30)


@pytest.mark.asyncio
async def test_list_month_audit_log_keeps_to_whose_month_it_is() -> None:
    use_case = build(
        [
            an_entry(date(2026, 9, 3), datetime(2026, 9, 3, 9, 0), target_user_id=1),
            an_entry(date(2026, 9, 3), datetime(2026, 9, 3, 10, 0), target_user_id=2),
        ]
    )

    page = await use_case.execute(target_user_id=1, month=SEPTEMBER, limit=50, offset=0)

    assert page.total == 1
    assert page.entries[0].log.target_user_id == 1


@pytest.mark.asyncio
async def test_list_month_audit_log_names_the_mission_each_line_is_about() -> None:
    """Whose month it is, the screen already says; what was booked, it does not."""
    use_case = build(
        [
            an_entry(date(2026, 9, 3), datetime(2026, 9, 3, 9, 0), project_id=10),
            an_entry(date(2026, 9, 4), datetime(2026, 9, 4, 9, 0), project_id=11),
        ]
    )

    page = await use_case.execute(target_user_id=1, month=SEPTEMBER, limit=50, offset=0)

    # An archived mission still names the lines it carries: the month it was
    # booked on is read long after it left the reference list.
    assert [entry.project.label for entry in page.entries if entry.project] == [
        "NOMAD",
        "WAATcher",
    ]


@pytest.mark.asyncio
async def test_list_month_audit_log_survives_a_mission_that_was_deleted() -> None:
    use_case = build(
        [an_entry(date(2026, 9, 3), datetime(2026, 9, 3, 9, 0), project_id=99)]
    )

    page = await use_case.execute(target_user_id=1, month=SEPTEMBER, limit=50, offset=0)

    assert page.total == 1
    assert page.entries[0].project is None


@pytest.mark.asyncio
async def test_list_month_audit_log_carries_what_holds_for_the_whole_month() -> None:
    """Validating a month is dated by the month itself, and belongs to its log."""
    use_case = build(
        [
            AuditLog(
                action=AuditAction.MONTH_VALIDATE,
                actor_id=1,
                target_user_id=1,
                day=SEPTEMBER,
                at=datetime(2026, 10, 1, 9, 0),
            )
        ]
    )

    page = await use_case.execute(target_user_id=1, month=SEPTEMBER, limit=50, offset=0)

    assert page.entries[0].log.action is AuditAction.MONTH_VALIDATE
    assert page.entries[0].project is None


@pytest.mark.asyncio
async def test_list_month_audit_log_counts_the_month_and_serves_one_page() -> None:
    use_case = build(
        [
            an_entry(date(2026, 9, rank), datetime(2026, 9, rank, 9, 0))
            for rank in range(1, 6)
        ]
    )

    page = await use_case.execute(target_user_id=1, month=SEPTEMBER, limit=2, offset=2)

    assert page.total == 5
    assert [entry.log.day.day for entry in page.entries if entry.log.day] == [3, 2]


@pytest.mark.asyncio
async def test_list_month_audit_log_still_signs_a_deactivated_account() -> None:
    use_case = build(
        [an_entry(date(2026, 9, 3), datetime(2026, 9, 3, 9, 0), target_user_id=2)]
    )

    page = await use_case.execute(target_user_id=2, month=SEPTEMBER, limit=50, offset=0)

    assert page.entries[0].target_user == NINO
