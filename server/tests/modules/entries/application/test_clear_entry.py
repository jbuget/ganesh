"""Suppression d'une saisie."""

from datetime import date

import pytest

from src.modules.entries.application.dtos.set_entry_dto import (
    ClearEntryCommand,
    SetEntryCommand,
)
from src.modules.entries.application.use_cases.clear_entry import ClearEntryUseCase
from src.modules.entries.application.use_cases.set_entry import SetEntryUseCase
from src.modules.entries.domain.entities.entry import DayValue, Entry
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
PROJECT = Project(
    id=10, label="Portail", kind=ProjectKind.PROJET, statut=ProjectStatus.CADRAGE
)
JOUR = date(2026, 9, 15)


def build(entries: list[Entry] | None = None, months: list[Month] | None = None):
    users = InMemoryUserRepository([ALICE])
    entry_repo = InMemoryEntryRepository(entries or [])
    month_repo = InMemoryMonthRepository(months or [])
    audit = InMemoryAuditLogRepository()
    clear = ClearEntryUseCase(
        users=users, entries=entry_repo, months=month_repo, audit_logs=audit
    )
    set_entry = SetEntryUseCase(
        users=users,
        projects=InMemoryProjectRepository([PROJECT]),
        entries=entry_repo,
        months=month_repo,
        audit_logs=audit,
    )
    return clear, set_entry, entry_repo, audit


def an_entry(jour: date = JOUR, valeur: float = 1.0) -> Entry:
    return Entry(
        id=1,
        user_id=1,
        project_id=10,
        jour=jour,
        valeur=DayValue(valeur),
        statut_at_entry=ProjectStatus.CADRAGE,
    )


async def test_an_entry_is_removed() -> None:
    clear, _, entries, _ = build([an_entry()])

    await clear.execute(
        ClearEntryCommand(actor_id=1, target_user_id=1, project_id=10, jour=JOUR)
    )

    assert await entries.get(1, 10, JOUR) is None


async def test_clearing_an_empty_cell_is_harmless() -> None:
    """Le cycle de saisie repasse par le vide : l'operation doit rester sure."""
    clear, _, entries, _ = build()

    await clear.execute(
        ClearEntryCommand(actor_id=1, target_user_id=1, project_id=10, jour=JOUR)
    )

    assert await entries.get(1, 10, JOUR) is None


async def test_removal_is_traced_with_the_previous_value() -> None:
    clear, _, _, audit = build([an_entry(valeur=0.5)])

    await clear.execute(
        ClearEntryCommand(actor_id=1, target_user_id=1, project_id=10, jour=JOUR)
    )

    log = audit.logs[-1]
    assert log.action.value == "entry.clear"
    assert log.old_value == "0.5"


async def test_clearing_an_empty_cell_leaves_no_trace() -> None:
    clear, _, _, audit = build()

    await clear.execute(
        ClearEntryCommand(actor_id=1, target_user_id=1, project_id=10, jour=JOUR)
    )

    assert audit.logs == []


async def test_a_validated_month_refuses_removal() -> None:
    month = Month(user_id=1, mois=date(2026, 9, 1))
    month.validate(by=ALICE)
    clear, _, entries, _ = build([an_entry()], months=[month])

    with pytest.raises(ForbiddenActionError):
        await clear.execute(
            ClearEntryCommand(actor_id=1, target_user_id=1, project_id=10, jour=JOUR)
        )

    assert await entries.get(1, 10, JOUR) is not None


async def test_an_unknown_actor_is_rejected() -> None:
    clear, _, _, _ = build([an_entry()])

    with pytest.raises(EntityNotFoundError):
        await clear.execute(
            ClearEntryCommand(actor_id=99, target_user_id=1, project_id=10, jour=JOUR)
        )


async def test_a_non_working_day_can_still_be_cleaned_up() -> None:
    """On interdit de saisir un samedi, jamais d'en retirer une saisie heritee."""
    samedi = date(2026, 9, 12)
    clear, _, entries, _ = build([an_entry(jour=samedi)])

    await clear.execute(
        ClearEntryCommand(actor_id=1, target_user_id=1, project_id=10, jour=samedi)
    )

    assert await entries.get(1, 10, samedi) is None


async def test_a_full_cycle_returns_the_cell_to_empty() -> None:
    """Vide -> demi -> pleine -> vide : le tour complet du clic."""
    clear, set_entry, entries, _ = build()
    for valeur in (0.5, 1.0):
        await set_entry.execute(
            SetEntryCommand(
                actor_id=1, target_user_id=1, project_id=10, jour=JOUR, valeur=valeur
            )
        )

    await clear.execute(
        ClearEntryCommand(actor_id=1, target_user_id=1, project_id=10, jour=JOUR)
    )

    assert await entries.get(1, 10, JOUR) is None
