"""La fiche d'une mission : ce qu'elle rassemble."""

from datetime import date

import pytest

from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.projects.application.use_cases.get_project_detail import (
    GetProjectDetailUseCase,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from tests.helpers.in_memory_repositories import (
    InMemoryEntryRepository,
    InMemoryProjectAssigneeRepository,
    InMemoryProjectDetailRepository,
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
NINO = User(
    id=2,
    entra_oid="oid-2",
    email="n.garo.ext@waat.fr",
    display_name="N. Garo",
    role=Role.TEAMMATE,
)
PROJECT = Project(
    id=10, label="Portail", kind=ProjectKind.PROJET, statut=ProjectStatus.REALISATION
)


def saisie(user_id: int, jour: date, valeur: float = 1.0) -> Entry:
    return Entry(
        id=None,
        user_id=user_id,
        project_id=10,
        jour=jour,
        valeur=DayValue(valeur),
        statut_at_entry=ProjectStatus.REALISATION,
    )


def build(entries: list[Entry] | None = None, affectations=None):
    return GetProjectDetailUseCase(
        projects=InMemoryProjectRepository([PROJECT]),
        details=InMemoryProjectDetailRepository(),
        assignees=InMemoryProjectAssigneeRepository(affectations or {}),
        entries=InMemoryEntryRepository(entries or []),
        users=InMemoryUserRepository([ALICE, NINO]),
    )


async def test_an_unknown_mission_is_refused() -> None:
    with pytest.raises(EntityNotFoundError):
        await build().execute(99)


async def test_the_biggest_contributor_comes_first() -> None:
    detail = await build(
        [
            saisie(1, date(2026, 9, 14)),
            saisie(2, date(2026, 9, 14)),
            saisie(2, date(2026, 9, 15)),
        ]
    ).execute(10)

    assert [c.user.display_name for c in detail.contributions] == ["N. Garo", "L. Chen"]
    assert [c.jours for c in detail.contributions] == [2.0, 1.0]


async def test_a_contribution_is_split_by_month() -> None:
    detail = await build(
        [
            saisie(1, date(2026, 8, 31), 0.5),
            saisie(1, date(2026, 9, 14)),
            saisie(1, date(2026, 9, 15), 0.5),
        ]
    ).execute(10)

    assert detail.contributions[0].par_mois == [
        (date(2026, 9, 1), 1.5),
        (date(2026, 8, 1), 0.5),
    ]


async def test_the_most_recent_month_comes_first() -> None:
    """On lit d'abord ce qui vient de se passer."""
    detail = await build(
        [saisie(1, date(2026, 7, 1)), saisie(1, date(2026, 12, 1))]
    ).execute(10)

    assert [mois for mois, _ in detail.contributions[0].par_mois] == [
        date(2026, 12, 1),
        date(2026, 7, 1),
    ]


async def test_someone_who_never_declared_time_is_absent() -> None:
    """Etre affecte ne suffit pas a figurer dans la consommation."""
    detail = await build(affectations={(10, ProjectRole.INTERVENANT): [1, 2]}).execute(
        10
    )

    assert detail.contributions == []
    assert len(detail.intervenants) == 2


async def test_referents_and_intervenants_are_told_apart() -> None:
    detail = await build(
        affectations={
            (10, ProjectRole.REFERENT): [1],
            (10, ProjectRole.INTERVENANT): [2],
        }
    ).execute(10)

    assert [u.display_name for u in detail.referents] == ["L. Chen"]
    assert [u.display_name for u in detail.intervenants] == ["N. Garo"]
