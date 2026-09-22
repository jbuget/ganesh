"""Taking one of one's own rhythms back out of the register."""

from datetime import date

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.calendar.domain.entities.week_pattern import WeekPattern
from src.modules.users.application.dtos.user_dto import WithdrawOwnRhythmCommand
from src.modules.users.application.use_cases.withdraw_own_rhythm import (
    WithdrawOwnRhythmUseCase,
)
from src.modules.users.domain.entities.rhythm import Rhythm
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryRhythmRepository,
    InMemoryUserRepository,
)

OCTOBER = date(2026, 10, 5)
TEAMMATE_ID = 2
SOMEBODY_ELSE = 3


def a_user(user_id: int, is_active: bool = True) -> User:
    return User(
        id=user_id,
        entra_oid=f"oid-{user_id}",
        email=f"user{user_id}@waat.fr",
        display_name="L. Chen",
        role=Role.TEAMMATE,
        is_active=is_active,
    )


def a_rhythm(user_id: int, effective_from: date = OCTOBER) -> Rhythm:
    return Rhythm(
        id=None,
        user_id=user_id,
        pattern=WeekPattern(monday=0.0, tuesday=0.0),
        effective_from=effective_from,
    )


def build(users: list[User], rhythms: list[Rhythm]):
    people = InMemoryUserRepository(users)
    store = InMemoryRhythmRepository(rhythms)
    audit = InMemoryAuditLogRepository()
    return (
        WithdrawOwnRhythmUseCase(users=people, rhythms=store, audit_logs=audit),
        store,
        audit,
    )


async def test_a_teammate_takes_back_a_rhythm_they_declared() -> None:
    use_case, store, _ = build([a_user(TEAMMATE_ID)], [a_rhythm(TEAMMATE_ID)])

    await use_case.execute(
        WithdrawOwnRhythmCommand(actor_id=TEAMMATE_ID, effective_from=OCTOBER)
    )

    assert (await store.history_of(TEAMMATE_ID)).newest_first == ()


async def test_withdrawing_a_rhythm_is_traced() -> None:
    use_case, _, audit = build([a_user(TEAMMATE_ID)], [a_rhythm(TEAMMATE_ID)])

    await use_case.execute(
        WithdrawOwnRhythmCommand(actor_id=TEAMMATE_ID, effective_from=OCTOBER)
    )

    logged = audit.logs[-1]
    assert logged.action is AuditAction.USER_RHYTHM_WITHDRAW
    assert logged.actor_id == TEAMMATE_ID
    assert logged.target_user_id == TEAMMATE_ID
    assert logged.payload["effective_from"] == "2026-10-05"


async def test_a_rhythm_that_is_not_there_is_said_so() -> None:
    # Silence would read as a withdrawal, and the screen would stop showing
    # a row that is still in the register.
    use_case, _, _ = build([a_user(TEAMMATE_ID)], [])

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(
            WithdrawOwnRhythmCommand(actor_id=TEAMMATE_ID, effective_from=OCTOBER)
        )


async def test_nobody_reaches_a_colleague_s_rhythm() -> None:
    # The command carries no target, so the only rhythm it can name is the
    # actor's own: a colleague's, opening the very same day, stays put.
    use_case, store, _ = build(
        [a_user(TEAMMATE_ID), a_user(SOMEBODY_ELSE)],
        [a_rhythm(SOMEBODY_ELSE)],
    )

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(
            WithdrawOwnRhythmCommand(actor_id=TEAMMATE_ID, effective_from=OCTOBER)
        )

    assert len((await store.history_of(SOMEBODY_ELSE)).newest_first) == 1


async def test_a_deactivated_account_withdraws_nothing() -> None:
    use_case, _, _ = build(
        [a_user(TEAMMATE_ID, is_active=False)], [a_rhythm(TEAMMATE_ID)]
    )

    with pytest.raises(ForbiddenActionError):
        await use_case.execute(
            WithdrawOwnRhythmCommand(actor_id=TEAMMATE_ID, effective_from=OCTOBER)
        )
