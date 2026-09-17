"""Retrait d'une mission entiere d'un mois."""

from datetime import date

import pytest

from src.modules.entries.application.dtos.set_entry_dto import RemoveMissionCommand
from src.modules.entries.application.use_cases.remove_mission_from_month import (
    RemoveMissionFromMonthUseCase,
)
from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.months.domain.entities.month import Month
from src.modules.projects.domain.entities.project import ProjectStatus
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryEntryRepository,
    InMemoryMonthRepository,
    InMemoryUserRepository,
)

ALICE = User(
    id=1,
    entra_oid="oid-1",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)
MOIS = date(2026, 9, 1)


def build(entries: list[Entry] | None = None, months: list[Month] | None = None):
    users = InMemoryUserRepository([ALICE])
    entry_repo = InMemoryEntryRepository(entries or [])
    audit = InMemoryAuditLogRepository()
    use_case = RemoveMissionFromMonthUseCase(
        users=users,
        entries=entry_repo,
        months=InMemoryMonthRepository(months or []),
        audit_logs=audit,
    )
    return use_case, entry_repo, audit


def an_entry(
    day: int, value: float = 1.0, project_id: int = 10, entry_id: int = 1
) -> Entry:
    return Entry(
        id=entry_id,
        user_id=1,
        project_id=project_id,
        day=date(2026, 9, day),
        value=DayValue(value),
        status_at_entry=ProjectStatus.SCOPING,
    )


def a_command(project_id: int = 10) -> RemoveMissionCommand:
    return RemoveMissionCommand(
        actor_id=1, target_user_id=1, project_id=project_id, month=MOIS
    )


async def test_every_entry_of_the_mission_is_removed() -> None:
    use_case, entries, _ = build(
        [an_entry(14, entry_id=1), an_entry(15, value=0.5, entry_id=2)]
    )

    await use_case.execute(a_command())

    assert await entries.list_for_month(1, MOIS) == []


async def test_the_other_missions_of_the_month_are_left_alone() -> None:
    autre = an_entry(14, project_id=11, entry_id=2)
    use_case, entries, _ = build([an_entry(14, entry_id=1), autre])

    await use_case.execute(a_command())

    assert await entries.list_for_month(1, MOIS) == [autre]


async def test_the_removed_days_are_counted_back() -> None:
    """L'ecran annonce ce qui sera perdu : le compte doit venir du domaine."""
    use_case, _, _ = build([an_entry(14), an_entry(15, value=0.5, entry_id=2)])

    assert await use_case.execute(a_command()) == 1.5


async def test_removing_a_mission_without_entries_is_harmless() -> None:
    use_case, _, audit = build()

    assert await use_case.execute(a_command()) == 0
    assert audit.logs == []


async def test_each_removal_is_traced_with_its_previous_value() -> None:
    use_case, _, audit = build([an_entry(14), an_entry(15, value=0.5, entry_id=2)])

    await use_case.execute(a_command())

    assert [log.action.value for log in audit.logs] == ["entry.clear", "entry.clear"]
    assert sorted(log.old_value for log in audit.logs) == ["0.5", "1.0"]


async def test_a_validated_month_refuses_the_removal() -> None:
    month = Month(user_id=1, month=MOIS)
    month.validate(by=ALICE)
    use_case, entries, _ = build([an_entry(14)], months=[month])

    with pytest.raises(ForbiddenActionError):
        await use_case.execute(a_command())

    assert len(await entries.list_for_month(1, MOIS)) == 1


async def test_an_unknown_actor_is_refused() -> None:
    use_case, _, _ = build([an_entry(14)])

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(
            RemoveMissionCommand(
                actor_id=99, target_user_id=1, project_id=10, month=MOIS
            )
        )
