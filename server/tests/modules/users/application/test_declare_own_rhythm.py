"""Declaring one's own rhythm, and nobody else's."""

from datetime import date

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.calendar.domain.entities.week_pattern import WeekPattern
from src.modules.users.application.dtos.user_dto import DeclareOwnRhythmCommand
from src.modules.users.application.use_cases.declare_own_rhythm import (
    DeclareOwnRhythmUseCase,
)
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

SEPTEMBER = date(2026, 9, 1)
WEDNESDAY = date(2026, 9, 16)
FOUR_FIFTHS = WeekPattern(wednesday=0.0)


def make_teammate(is_active: bool = True) -> User:
    return User(
        id=2,
        entra_oid="oid-teammate",
        email="l.chen@waat.fr",
        display_name="L. Chen",
        role=Role.TEAMMATE,
        is_active=is_active,
    )


def build(users: list[User]):
    people = InMemoryUserRepository(users)
    rhythms = InMemoryRhythmRepository()
    audit = InMemoryAuditLogRepository()
    use_case = DeclareOwnRhythmUseCase(users=people, rhythms=rhythms, audit_logs=audit)
    return use_case, rhythms, audit


def command(**overrides) -> DeclareOwnRhythmCommand:
    fields: dict = {
        "actor_id": 2,
        "pattern": FOUR_FIFTHS,
        "effective_from": SEPTEMBER,
    }
    fields.update(overrides)
    return DeclareOwnRhythmCommand(**fields)


async def test_a_teammate_declares_their_own_rhythm() -> None:
    use_case, rhythms, _ = build([make_teammate()])

    declared = await use_case.execute(command())

    assert declared.pattern == FOUR_FIFTHS
    assert (await rhythms.history_of(2)).on(WEDNESDAY) == 0.0


async def test_a_rhythm_is_written_for_the_one_who_declared_it() -> None:
    # The command carries no target: there is no colleague to hit by mistake.
    use_case, _, _ = build([make_teammate()])

    declared = await use_case.execute(command())

    assert declared.user_id == 2


async def test_declaring_a_rhythm_is_traced() -> None:
    use_case, _, audit = build([make_teammate()])

    await use_case.execute(command())

    logged = audit.logs[-1]
    assert logged.action is AuditAction.USER_RHYTHM_DECLARE
    assert logged.actor_id == 2
    assert logged.target_user_id == 2
    assert logged.payload["effective_from"] == "2026-09-01"
    assert logged.payload["wednesday"] == 0.0


async def test_an_unknown_actor_declares_nothing() -> None:
    use_case, _, _ = build([])

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(command())


async def test_a_deactivated_account_declares_nothing() -> None:
    use_case, _, _ = build([make_teammate(is_active=False)])

    with pytest.raises(ForbiddenActionError):
        await use_case.execute(command())
