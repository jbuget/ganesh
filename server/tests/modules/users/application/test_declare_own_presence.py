"""Saying which days one works, and from where. One's own week, and no other."""

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.users.application.dtos.user_dto import DeclareOwnPresenceCommand
from src.modules.users.application.use_cases.declare_own_presence import (
    DeclareOwnPresenceUseCase,
)
from src.modules.users.domain.entities.presence import DayPresence, WeekPresence
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryUserRepository,
)

WEEK = WeekPresence(wednesday=DayPresence.REMOTE, friday=DayPresence.AWAY)


def a_teammate(is_active: bool = True) -> User:
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
    audit = InMemoryAuditLogRepository()
    return DeclareOwnPresenceUseCase(users=people, audit_logs=audit), people, audit


async def test_a_teammate_says_their_own_week() -> None:
    use_case, people, _ = build([a_teammate()])

    said = await use_case.execute(DeclareOwnPresenceCommand(actor_id=2, week=WEEK))

    assert said.presence == WEEK
    stored = await people.get_by_id(2)
    assert stored is not None and stored.presence is not None
    assert stored.presence.days_on_site == 3


async def test_a_week_is_written_for_the_one_who_said_it() -> None:
    # The command carries no target: there is no colleague to reach by mistake.
    use_case, _, _ = build([a_teammate()])

    said = await use_case.execute(DeclareOwnPresenceCommand(actor_id=2, week=WEEK))

    assert said.id == 2


async def test_saying_one_s_week_is_traced() -> None:
    use_case, _, audit = build([a_teammate()])

    await use_case.execute(DeclareOwnPresenceCommand(actor_id=2, week=WEEK))

    logged = audit.logs[-1]
    assert logged.action is AuditAction.USER_PRESENCE_DECLARE
    assert logged.actor_id == 2
    assert logged.target_user_id == 2
    assert logged.payload["wednesday"] == "REMOTE"


async def test_an_unknown_actor_says_nothing() -> None:
    use_case, _, _ = build([])

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(DeclareOwnPresenceCommand(actor_id=2, week=WEEK))


async def test_a_deactivated_account_says_nothing() -> None:
    use_case, _, _ = build([a_teammate(is_active=False)])

    with pytest.raises(ForbiddenActionError):
        await use_case.execute(DeclareOwnPresenceCommand(actor_id=2, week=WEEK))
