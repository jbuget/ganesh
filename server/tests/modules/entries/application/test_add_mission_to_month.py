"""Putting a mission on a month, before any time is entered on it."""

from datetime import date

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.entries.application.dtos.set_entry_dto import AddMissionCommand
from src.modules.entries.application.use_cases.add_mission_to_month import (
    AddMissionToMonthUseCase,
)
from src.modules.months.domain.entities.month import Month
from src.modules.notifications.domain.services.delivery import NotificationDelivery
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
    InMemoryMonthRepository,
    InMemoryNotificationRepository,
    InMemoryProjectRepository,
    InMemoryUserMissionRepository,
    InMemoryUserRepository,
)

ALICE = User(
    id=1,
    entra_oid="oid-1",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)
PORTAIL = Project(
    id=10,
    label="Portail",
    kind=ProjectKind.PROJECT,
    status=ProjectStatus.DEVELOPMENT,
)
MONTH = date(2026, 9, 1)


def build(months: list[Month] | None = None):
    use_case, rows, _ = build_with_audit(months)
    return use_case, rows


def build_with_audit(months: list[Month] | None = None):
    rows = InMemoryUserMissionRepository()
    audit = InMemoryAuditLogRepository()
    use_case = AddMissionToMonthUseCase(
        users=InMemoryUserRepository([ALICE]),
        projects=InMemoryProjectRepository([PORTAIL]),
        months=InMemoryMonthRepository(months or []),
        user_missions=rows,
        audit_logs=audit,
        notifications=NotificationDelivery(InMemoryNotificationRepository()),
    )
    return use_case, rows, audit


def a_command(project_id: int = 10, actor_id: int = 1) -> AddMissionCommand:
    return AddMissionCommand(
        actor_id=actor_id,
        target_user_id=1,
        project_id=project_id,
        activity_id=None,
        month=MONTH,
    )


async def test_the_mission_is_put_on_the_month() -> None:
    use_case, rows = build()

    await use_case.execute(a_command())

    assert await rows.list_for_month(1, MONTH) == [(10, None)]


async def test_any_day_of_the_month_puts_the_mission_on_that_month() -> None:
    """The screen speaks of a month, whatever day it hands over."""
    use_case, rows = build()

    await use_case.execute(
        AddMissionCommand(
            actor_id=1,
            target_user_id=1,
            project_id=10,
            activity_id=None,
            month=date(2026, 9, 24),
        )
    )

    assert await rows.list_for_month(1, MONTH) == [(10, None)]


async def test_adding_the_same_mission_twice_leaves_one_row() -> None:
    use_case, rows = build()

    await use_case.execute(a_command())
    await use_case.execute(a_command())

    assert await rows.list_for_month(1, MONTH) == [(10, None)]


async def test_a_validated_month_refuses_a_new_mission() -> None:
    month = Month(user_id=1, month=MONTH)
    month.validate(by=ALICE)
    use_case, rows = build(months=[month])

    with pytest.raises(ForbiddenActionError):
        await use_case.execute(a_command())

    assert await rows.list_for_month(1, MONTH) == []


async def test_an_unknown_mission_is_refused() -> None:
    use_case, _ = build()

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(a_command(project_id=99))


async def test_an_unknown_actor_is_refused() -> None:
    use_case, _ = build()

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(a_command(actor_id=99))


async def test_a_deactivated_actor_is_refused() -> None:
    deactivated = User(
        id=2,
        entra_oid="oid-2",
        email="m.roux@waat.fr",
        display_name="M. Roux",
        role=Role.TEAMMATE,
        is_active=False,
    )
    rows = InMemoryUserMissionRepository()
    use_case = AddMissionToMonthUseCase(
        users=InMemoryUserRepository([ALICE, deactivated]),
        projects=InMemoryProjectRepository([PORTAIL]),
        months=InMemoryMonthRepository(),
        user_missions=rows,
        audit_logs=InMemoryAuditLogRepository(),
        notifications=NotificationDelivery(InMemoryNotificationRepository()),
    )

    with pytest.raises(ForbiddenActionError):
        await use_case.execute(
            AddMissionCommand(
                actor_id=2,
                target_user_id=1,
                project_id=10,
                activity_id=None,
                month=MONTH,
            )
        )


async def test_lining_up_a_project_on_a_month_is_traced() -> None:
    """Preparing a month is a gesture of its own, and it leaves a trace.

    It is read in the project's own log too: knowing who put it on their month,
    before any day was booked on it, says when people started counting on it.
    """
    use_case, _, audit = build_with_audit()

    await use_case.execute(a_command())

    (trace,) = audit.logs
    assert trace.action is AuditAction.MONTH_PROJECT_ADD
    assert (trace.actor_id, trace.target_user_id, trace.project_id) == (1, 1, 10)
    assert trace.day == MONTH


async def test_the_trace_names_the_month_by_its_first_day() -> None:
    use_case, _, audit = build_with_audit()

    await use_case.execute(
        AddMissionCommand(
            actor_id=1,
            target_user_id=1,
            project_id=10,
            activity_id=None,
            month=date(2026, 9, 23),
        )
    )

    assert audit.logs[0].day == MONTH
