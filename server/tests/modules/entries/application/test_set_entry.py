"""Enregistrement d'une saisie de temps."""

from datetime import date

import pytest

from src.modules.entries.application.dtos.set_entry_dto import SetEntryCommand
from src.modules.entries.application.use_cases.set_entry import SetEntryUseCase
from src.modules.months.domain.entities.month import Month
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
    ValidationError,
)
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryEntryRepository,
    InMemoryMonthRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
)

ALICE = User(
    id=1,
    entra_oid="oid-1",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)
BOB = User(
    id=2,
    entra_oid="oid-2",
    email="g.belhadj@waat.fr",
    display_name="G. Belhadj",
    role=Role.TEAMMATE,
)
PROJECT = Project(
    id=10,
    label="Portail bailleurs",
    kind=ProjectKind.PROJET,
    statut=ProjectStatus.CADRAGE,
)
JOUR = date(2026, 9, 15)


def build(months: list[Month] | None = None):
    users = InMemoryUserRepository([ALICE, BOB])
    projects = InMemoryProjectRepository([PROJECT])
    entries = InMemoryEntryRepository()
    month_repo = InMemoryMonthRepository(months or [])
    audit = InMemoryAuditLogRepository()
    use_case = SetEntryUseCase(
        users=users,
        projects=projects,
        entries=entries,
        months=month_repo,
        audit_logs=audit,
    )
    return use_case, entries, audit, month_repo


async def test_a_user_records_time_on_their_own_month() -> None:
    use_case, entries, _, _ = build()

    await use_case.execute(
        SetEntryCommand(
            actor_id=1, target_user_id=1, project_id=10, jour=JOUR, valeur=0.5
        )
    )

    saved = await entries.get(1, 10, JOUR)
    assert saved is not None
    assert saved.valeur == 0.5


async def test_the_entry_captures_the_current_project_phase() -> None:
    use_case, entries, _, _ = build()

    await use_case.execute(
        SetEntryCommand(
            actor_id=1, target_user_id=1, project_id=10, jour=JOUR, valeur=1.0
        )
    )

    saved = await entries.get(1, 10, JOUR)
    assert saved is not None
    assert saved.statut_at_entry is ProjectStatus.CADRAGE


async def test_a_user_can_record_time_on_a_colleague_open_month() -> None:
    """Transparence assumee : chacun peut corriger le mois ouvert d'un autre."""
    use_case, entries, _, _ = build()

    await use_case.execute(
        SetEntryCommand(
            actor_id=1, target_user_id=2, project_id=10, jour=JOUR, valeur=1.0
        )
    )

    assert await entries.get(2, 10, JOUR) is not None


async def test_writing_to_a_validated_month_is_rejected() -> None:
    month = Month(user_id=1, mois=date(2026, 9, 1))
    month.validate(by=ALICE)
    use_case, entries, _, _ = build(months=[month])

    with pytest.raises(ForbiddenActionError):
        await use_case.execute(
            SetEntryCommand(
                actor_id=1, target_user_id=1, project_id=10, jour=JOUR, valeur=1.0
            )
        )

    assert await entries.get(1, 10, JOUR) is None


async def test_an_invalid_value_is_rejected() -> None:
    use_case, _, _, _ = build()

    with pytest.raises(ValidationError):
        await use_case.execute(
            SetEntryCommand(
                actor_id=1, target_user_id=1, project_id=10, jour=JOUR, valeur=0.75
            )
        )


async def test_an_unknown_project_is_rejected() -> None:
    use_case, _, _, _ = build()

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(
            SetEntryCommand(
                actor_id=1, target_user_id=1, project_id=999, jour=JOUR, valeur=1.0
            )
        )


async def test_setting_a_value_twice_overwrites_it() -> None:
    use_case, entries, _, _ = build()
    command = SetEntryCommand(
        actor_id=1, target_user_id=1, project_id=10, jour=JOUR, valeur=0.5
    )
    await use_case.execute(command)

    await use_case.execute(
        SetEntryCommand(
            actor_id=1, target_user_id=1, project_id=10, jour=JOUR, valeur=1.0
        )
    )

    saved = await entries.get(1, 10, JOUR)
    assert saved is not None
    assert saved.valeur == 1.0
    assert len(await entries.list_for_month(1, JOUR)) == 1


async def test_every_entry_is_traced() -> None:
    use_case, _, audit, _ = build()

    await use_case.execute(
        SetEntryCommand(
            actor_id=1, target_user_id=2, project_id=10, jour=JOUR, valeur=1.0
        )
    )

    assert len(audit.logs) == 1
    log = audit.logs[0]
    assert log.actor_id == 1
    assert log.target_user_id == 2
    assert log.new_value == "1.0"
    assert log.is_on_behalf_of_someone_else is True


async def test_overwriting_traces_the_previous_value() -> None:
    use_case, _, audit, _ = build()
    base = SetEntryCommand(
        actor_id=1, target_user_id=1, project_id=10, jour=JOUR, valeur=0.5
    )
    await use_case.execute(base)

    await use_case.execute(
        SetEntryCommand(
            actor_id=1, target_user_id=1, project_id=10, jour=JOUR, valeur=1.0
        )
    )

    assert audit.logs[-1].old_value == "0.5"
    assert audit.logs[-1].new_value == "1.0"


async def test_recording_time_opens_the_month_implicitly() -> None:
    use_case, _, _, months = build()

    await use_case.execute(
        SetEntryCommand(
            actor_id=1, target_user_id=1, project_id=10, jour=JOUR, valeur=1.0
        )
    )

    month = await months.get(1, date(2026, 9, 1))
    assert month is not None
    assert month.is_writable is True


async def test_an_inactive_user_cannot_record_time() -> None:
    use_case, _, _, _ = build()
    ALICE.actif = False

    try:
        with pytest.raises(ForbiddenActionError):
            await use_case.execute(
                SetEntryCommand(
                    actor_id=1, target_user_id=1, project_id=10, jour=JOUR, valeur=1.0
                )
            )
    finally:
        ALICE.actif = True
