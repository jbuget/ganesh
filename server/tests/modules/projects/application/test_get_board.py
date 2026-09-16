"""Assemblage du tableau de bord des projets."""

from datetime import date

from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.projects.application.use_cases.get_board import GetBoardUseCase
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryEntryRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
)

ALICE = User(
    id=1,
    entra_oid="a",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)
BOB = User(
    id=2,
    entra_oid="b",
    email="d.dehe@waat.fr",
    display_name="D. Dehe",
    role=Role.TEAMMATE,
)
AUJOURDHUI = date(2026, 9, 16)


def carte(id_: int, statut=ProjectStatus.CADRAGE, position=0, **kwargs) -> Project:
    return Project(
        id=id_,
        label=f"Mission {id_}",
        kind=ProjectKind.PROJET,
        statut=statut,
        position=position,
        **kwargs,
    )


def saisie(user_id: int, project_id: int, jour: date, valeur=1.0) -> Entry:
    return Entry(
        id=None,
        user_id=user_id,
        project_id=project_id,
        jour=jour,
        valeur=DayValue(valeur),
        statut_at_entry=ProjectStatus.CADRAGE,
    )


def build(projects: list[Project], entries: list[Entry] | None = None):
    return GetBoardUseCase(
        projects=InMemoryProjectRepository(projects),
        entries=InMemoryEntryRepository(entries or []),
        users=InMemoryUserRepository([ALICE, BOB]),
    )


async def test_every_phase_has_its_column_even_empty() -> None:
    """Une colonne absente empecherait d'y deposer une carte."""
    board = await build([]).execute(today=AUJOURDHUI)

    assert [c.statut for c in board.colonnes] == list(ProjectStatus)


async def test_cards_land_in_their_phase() -> None:
    board = await build(
        [
            carte(1, ProjectStatus.CADRAGE),
            carte(2, ProjectStatus.DEPLOIEMENT),
        ]
    ).execute(today=AUJOURDHUI)

    par_phase = {c.statut: [m.project.id for m in c.cartes] for c in board.colonnes}
    assert par_phase[ProjectStatus.CADRAGE] == [1]
    assert par_phase[ProjectStatus.DEPLOIEMENT] == [2]


async def test_cards_keep_the_order_chosen_by_the_team() -> None:
    board = await build(
        [
            carte(1, ProjectStatus.CADRAGE, position=2),
            carte(2, ProjectStatus.CADRAGE, position=0),
            carte(3, ProjectStatus.CADRAGE, position=1),
        ]
    ).execute(today=AUJOURDHUI)

    colonne = next(c for c in board.colonnes if c.statut is ProjectStatus.CADRAGE)
    assert [m.project.id for m in colonne.cartes] == [2, 3, 1]


async def test_equal_ranks_are_settled_by_label() -> None:
    """Les missions anterieures au tableau partagent toutes le rang 0."""
    board = await build(
        [
            Project(
                id=1,
                label="Zeta",
                kind=ProjectKind.PROJET,
                statut=ProjectStatus.CADRAGE,
                position=0,
            ),
            Project(
                id=2,
                label="Alpha",
                kind=ProjectKind.PROJET,
                statut=ProjectStatus.CADRAGE,
                position=0,
            ),
        ]
    ).execute(today=AUJOURDHUI)

    colonne = next(c for c in board.colonnes if c.statut is ProjectStatus.CADRAGE)
    assert [m.project.label for m in colonne.cartes] == ["Alpha", "Zeta"]


async def test_a_card_reports_the_time_consumed() -> None:
    board = await build(
        [carte(1)],
        [saisie(1, 1, date(2026, 9, 10)), saisie(2, 1, date(2026, 9, 11), 0.5)],
    ).execute(today=AUJOURDHUI)

    assert board.colonnes[1].cartes[0].consomme_j == 1.5


async def test_forecast_time_is_excluded_from_what_is_consumed() -> None:
    board = await build(
        [carte(1)],
        [saisie(1, 1, date(2026, 9, 10)), saisie(1, 1, date(2026, 12, 1))],
    ).execute(today=AUJOURDHUI)

    assert board.colonnes[1].cartes[0].consomme_j == 1.0


async def test_a_card_lists_who_worked_on_it() -> None:
    board = await build(
        [carte(1)],
        [saisie(1, 1, date(2026, 9, 10)), saisie(2, 1, date(2026, 9, 11))],
    ).execute(today=AUJOURDHUI)

    assert [c.display_name for c in board.colonnes[1].cartes[0].collaborateurs] == [
        "D. Dehe",
        "L. Chen",
    ]


async def test_someone_who_only_planned_time_already_counts() -> None:
    """Le previsionnel dit qui travaillera dessus : c'est une information utile."""
    board = await build([carte(1)], [saisie(2, 1, date(2026, 12, 1))]).execute(
        today=AUJOURDHUI
    )

    assert [c.display_name for c in board.colonnes[1].cartes[0].collaborateurs] == [
        "D. Dehe"
    ]


async def test_someone_appears_once_whatever_the_number_of_entries() -> None:
    board = await build(
        [carte(1)],
        [saisie(1, 1, date(2026, 9, 10)), saisie(1, 1, date(2026, 9, 11))],
    ).execute(today=AUJOURDHUI)

    assert len(board.colonnes[1].cartes[0].collaborateurs) == 1


async def test_a_card_carries_its_category_and_go_live_date() -> None:
    board = await build(
        [
            carte(
                1,
                categorie=ProjectCategory.INNOVER,
                date_mise_en_service=date(2026, 11, 15),
            )
        ]
    ).execute(today=AUJOURDHUI)

    mission = board.colonnes[1].cartes[0].project
    assert mission.categorie is ProjectCategory.INNOVER
    assert mission.date_mise_en_service == date(2026, 11, 15)


async def test_off_project_activities_never_appear() -> None:
    activite = Project(
        id=9, label="Absences", kind=ProjectKind.HORS_PROJET, statut=None
    )
    board = await build([carte(1), activite]).execute(today=AUJOURDHUI)

    toutes = [m.project.id for c in board.colonnes for m in c.cartes]
    assert toutes == [1]
