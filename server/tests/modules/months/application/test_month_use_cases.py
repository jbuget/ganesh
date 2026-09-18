"""Validating and reopening a month."""

from datetime import date

import pytest

from src.modules.months.application.dtos.month_dto import (
    ReopenMonthCommand,
    ValidateMonthCommand,
)
from src.modules.months.application.use_cases.reopen_month import ReopenMonthUseCase
from src.modules.months.application.use_cases.validate_month import ValidateMonthUseCase
from src.modules.months.domain.entities.month import Month, MonthState
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import ForbiddenActionError
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryMonthRepository,
    InMemoryUserRepository,
)

TEAMMATE = User(
    id=1,
    entra_oid="oid-1",
    email="d.dehe@waat.fr",
    display_name="D. Dehe",
    role=Role.TEAMMATE,
)
MANAGER = User(
    id=2,
    entra_oid="oid-2",
    email="j.buget@waat.fr",
    display_name="J. Buget",
    role=Role.MANAGER,
)
MOIS = date(2026, 9, 1)


def build(months: list[Month] | None = None):
    users = InMemoryUserRepository([TEAMMATE, MANAGER])
    month_repo = InMemoryMonthRepository(months or [])
    audit = InMemoryAuditLogRepository()
    return (
        ValidateMonthUseCase(users=users, months=month_repo, audit_logs=audit),
        ReopenMonthUseCase(users=users, months=month_repo, audit_logs=audit),
        month_repo,
        audit,
    )


async def test_a_user_validates_their_own_month() -> None:
    validate, _, months, _ = build()

    await validate.execute(
        ValidateMonthCommand(actor_id=1, target_user_id=1, month=MOIS)
    )

    month = await months.get(1, MOIS)
    assert month is not None
    assert month.state is MonthState.VALIDATED


async def test_validation_is_traced() -> None:
    validate, _, _, audit = build()

    await validate.execute(
        ValidateMonthCommand(actor_id=1, target_user_id=1, month=MOIS)
    )

    assert audit.logs[-1].action.value == "month.validate"


async def test_a_user_cannot_validate_someone_else_month() -> None:
    """One validates one's own month: validating for someone else makes no sense."""
    validate, _, _, _ = build()

    with pytest.raises(ForbiddenActionError):
        await validate.execute(
            ValidateMonthCommand(actor_id=1, target_user_id=2, month=MOIS)
        )


async def test_a_teammate_cannot_reopen_a_validated_month() -> None:
    validate, reopen, _, _ = build()
    await validate.execute(
        ValidateMonthCommand(actor_id=1, target_user_id=1, month=MOIS)
    )

    with pytest.raises(ForbiddenActionError):
        await reopen.execute(
            ReopenMonthCommand(actor_id=1, target_user_id=1, month=MOIS)
        )


async def test_a_manager_reopens_a_validated_month() -> None:
    validate, reopen, months, _ = build()
    await validate.execute(
        ValidateMonthCommand(actor_id=1, target_user_id=1, month=MOIS)
    )

    await reopen.execute(ReopenMonthCommand(actor_id=2, target_user_id=1, month=MOIS))

    month = await months.get(1, MOIS)
    assert month is not None
    assert month.is_writable is True
    assert month.reopened_by == 2


async def test_reopening_is_traced_with_its_author() -> None:
    validate, reopen, _, audit = build()
    await validate.execute(
        ValidateMonthCommand(actor_id=1, target_user_id=1, month=MOIS)
    )

    await reopen.execute(ReopenMonthCommand(actor_id=2, target_user_id=1, month=MOIS))

    log = audit.logs[-1]
    assert log.action.value == "month.reopen"
    assert log.actor_id == 2
    assert log.target_user_id == 1
