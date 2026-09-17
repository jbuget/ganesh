"""Assemblage du tableau de bord des projets."""

from datetime import date, datetime

from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.projects.application.use_cases.get_board import GetBoardUseCase
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryEntryRepository,
    InMemoryProjectAssigneeRepository,
    InMemoryProjectRepository,
    InMemoryProjectUpdateRepository,
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


def carte(
    id_: int,
    statut=ProjectStatus.CADRAGE,
    position=0,
    kind=ProjectKind.PROJET,
    **kwargs,
) -> Project:
    return Project(
        id=id_,
        label=f"Mission {id_}",
        kind=kind,
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


def build(
    projects: list[Project],
    entries: list[Entry] | None = None,
    affectations: dict[int, list[int]] | None = None,
    updates: InMemoryProjectUpdateRepository | None = None,
):
    return GetBoardUseCase(
        projects=InMemoryProjectRepository(projects),
        entries=InMemoryEntryRepository(entries or []),
        users=InMemoryUserRepository([ALICE, BOB]),
        assignees=InMemoryProjectAssigneeRepository(
            {
                (pid, ProjectRole.INTERVENANT): ids
                for pid, ids in (affectations or {}).items()
            }
        ),
        updates=updates or InMemoryProjectUpdateRepository(),
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


async def test_a_card_lists_the_people_expected_on_it() -> None:
    board = await build([carte(1)], affectations={1: [2, 1]}).execute(today=AUJOURDHUI)

    assert [c.display_name for c in board.colonnes[1].cartes[0].intervenants] == [
        "D. Dehe",
        "L. Chen",
    ]


async def test_time_spent_does_not_make_someone_an_intervenant() -> None:
    """Une mission peut avoir consomme des jours sans que personne n'y soit plus.

    C'est le cas d'un projet en exploitation : le temps passe appartient au
    passe, et le tableau ne doit pas laisser croire qu'on y travaille encore.
    """
    board = await build(
        [carte(1)], [saisie(1, 1, date(2026, 9, 10))], affectations={}
    ).execute(today=AUJOURDHUI)

    assert board.colonnes[1].cartes[0].intervenants == []
    assert board.colonnes[1].cartes[0].consomme_j == 1.0


async def test_someone_expected_soon_counts_without_any_entry() -> None:
    """On declare Nino sur un bug avant meme qu'il n'ait saisi la moindre heure."""
    board = await build([carte(1)], affectations={1: [2]}).execute(today=AUJOURDHUI)

    assert [c.display_name for c in board.colonnes[1].cartes[0].intervenants] == [
        "D. Dehe"
    ]


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


async def test_a_card_counts_the_updates_posted_on_it() -> None:
    """Le fil de suivi se lit d'un coup d'oeil, sans ouvrir la mission."""
    updates = InMemoryProjectUpdateRepository()
    await updates.add(
        ProjectUpdate(
            id=None,
            project_id=1,
            author_id=1,
            texte="Premier jet",
            publiee_le=datetime(2026, 9, 10, 9, 0),
        )
    )
    await updates.add(
        ProjectUpdate(
            id=None,
            project_id=1,
            author_id=2,
            texte="Relecture",
            publiee_le=datetime(2026, 9, 11, 9, 0),
        )
    )

    board = await build([carte(1), carte(2)], updates=updates).execute(today=AUJOURDHUI)

    par_mission = {c.project.id: c for c in board.colonnes[1].cartes}
    assert par_mission[1].commentaires == 2
    assert par_mission[2].commentaires == 0


async def test_a_removed_update_no_longer_counts() -> None:
    """Un message retire ne gonfle pas le compteur affiche sur la carte."""
    updates = InMemoryProjectUpdateRepository()
    maj = await updates.add(
        ProjectUpdate(
            id=None,
            project_id=1,
            author_id=1,
            texte="Premier jet",
            publiee_le=datetime(2026, 9, 10, 9, 0),
        )
    )
    maj.supprimer(par=1, a=datetime(2026, 9, 12, 9, 0))

    board = await build([carte(1)], updates=updates).execute(today=AUJOURDHUI)

    assert board.colonnes[1].cartes[0].commentaires == 0


async def test_a_card_counts_its_sub_projects() -> None:
    board = await build(
        [
            carte(1),
            carte(2, parent_id=1, kind=ProjectKind.LOT),
            carte(3, parent_id=1, kind=ProjectKind.LOT),
        ]
    ).execute(today=AUJOURDHUI)

    par_mission = {c.project.id: c for c in board.colonnes[1].cartes}
    assert par_mission[1].sous_projets == 2
    assert par_mission[2].sous_projets == 0


async def test_a_sub_project_card_names_its_parent() -> None:
    """Une carte de lot doit dire de quel projet elle releve."""
    board = await build(
        [carte(1), carte(2, parent_id=1, kind=ProjectKind.LOT)]
    ).execute(today=AUJOURDHUI)

    par_mission = {c.project.id: c for c in board.colonnes[1].cartes}
    assert par_mission[2].parent is not None
    assert par_mission[2].parent.id == 1
    assert par_mission[1].parent is None


async def test_an_inactive_parent_is_still_named() -> None:
    """Un lot survit a l'archivage de son parent : le lien doit tenir."""
    board = await build(
        [
            carte(1, actif=False),
            carte(2, parent_id=1, kind=ProjectKind.LOT),
        ]
    ).execute(today=AUJOURDHUI)

    cartes = {c.project.id: c for c in board.colonnes[1].cartes}
    assert 1 not in cartes
    assert cartes[2].parent is not None and cartes[2].parent.id == 1


async def test_archived_missions_stay_off_the_board_by_default() -> None:
    board = await build([carte(1), carte(2, actif=False)]).execute(today=AUJOURDHUI)

    assert [c.project.id for c in board.colonnes[1].cartes] == [1]


async def test_archived_missions_appear_when_asked_for() -> None:
    """On consulte les archivees pour faire le point, pas pour les piloter."""
    board = await build([carte(1), carte(2, actif=False)]).execute(
        today=AUJOURDHUI, include_inactive=True
    )

    assert [c.project.id for c in board.colonnes[1].cartes] == [1, 2]


async def test_archived_sub_projects_are_counted_only_when_shown() -> None:
    """Le compteur d'une carte dit ce que le tableau montre, rien de plus."""
    missions = [
        carte(1),
        carte(2, parent_id=1, kind=ProjectKind.LOT),
        carte(3, parent_id=1, kind=ProjectKind.LOT, actif=False),
    ]

    sans = await build(missions).execute(today=AUJOURDHUI)
    avec = await build(missions).execute(today=AUJOURDHUI, include_inactive=True)

    assert (
        next(c for c in sans.colonnes[1].cartes if c.project.id == 1).sous_projets == 1
    )
    assert (
        next(c for c in avec.colonnes[1].cartes if c.project.id == 1).sous_projets == 2
    )
