"""Ce que le referentiel affiche de chaque mission."""

from datetime import date, timedelta

from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.projects.application.use_cases.list_projects import ListProjectsUseCase
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryEntryRepository,
    InMemoryProjectAssigneeRepository,
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
PORTAIL = Project(
    id=10, label="Portail", kind=ProjectKind.PROJET, statut=ProjectStatus.CADRAGE
)


AUJOURDHUI = date(2026, 9, 17)


def saisie(jour: date, valeur: float = 1.0) -> Entry:
    return Entry(
        id=None,
        user_id=1,
        project_id=10,
        jour=jour,
        valeur=DayValue(valeur),
        statut_at_entry=ProjectStatus.CADRAGE,
    )


def build(affectations=None, entries: list[Entry] | None = None):
    return ListProjectsUseCase(
        projects=InMemoryProjectRepository([PORTAIL]),
        entries=InMemoryEntryRepository(entries or []),
        assignees=InMemoryProjectAssigneeRepository(affectations or {}),
        users=InMemoryUserRepository([ALICE, NINO]),
    )


async def test_a_mission_without_anyone_assigned_lists_nobody() -> None:
    listees = await build().execute()

    assert listees[0].referents == []
    assert listees[0].intervenants == []


async def test_referents_and_intervenants_are_told_apart() -> None:
    listees = await build(
        {
            (10, ProjectRole.REFERENT): [1],
            (10, ProjectRole.INTERVENANT): [2],
        }
    ).execute()

    assert [u.display_name for u in listees[0].referents] == ["L. Chen"]
    assert [u.display_name for u in listees[0].intervenants] == ["N. Garo"]


async def test_the_assigned_are_listed_in_alphabetical_order() -> None:
    """La liste se parcourt du regard : deux colonnes doivent s'aligner."""
    listees = await build({(10, ProjectRole.INTERVENANT): [2, 1]}).execute()

    assert [u.display_name for u in listees[0].intervenants] == ["L. Chen", "N. Garo"]


async def test_a_mission_nobody_declared_time_on_shows_nothing() -> None:
    listees = await build().execute(today=AUJOURDHUI)

    assert listees[0].realise_j == 0.0


async def test_the_declared_days_are_summed() -> None:
    listees = await build(
        entries=[saisie(AUJOURDHUI - timedelta(days=1)), saisie(AUJOURDHUI, 0.5)]
    ).execute(today=AUJOURDHUI)

    assert listees[0].realise_j == 1.5


async def test_a_day_to_come_is_forecast_and_stays_out() -> None:
    """Le realise ne doit jamais grossir de ce qui n'a pas encore ete fait."""
    listees = await build(
        entries=[saisie(AUJOURDHUI), saisie(AUJOURDHUI + timedelta(days=1))]
    ).execute(today=AUJOURDHUI)

    assert listees[0].realise_j == 1.0
