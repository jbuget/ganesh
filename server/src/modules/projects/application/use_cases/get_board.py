"""Assemble le tableau de bord des projets, par phase."""

from dataclasses import dataclass, field
from datetime import date

from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.projects.application.dtos.last_update import LastUpdate
from src.modules.projects.domain.entities.project import Project, ProjectStatus
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.projects.domain.repositories.project_assignee_repository import (
    ProjectAssigneeRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.repositories.project_update_repository import (
    ProjectUpdateRepository,
)
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository


@dataclass
class BoardCard:
    """Une carte du tableau : la mission et ce qu'on veut lire dessus."""

    project: Project
    consomme_j: float
    intervenants: list[User]
    #: Mises a jour vivantes du fil de suivi.
    commentaires: int = 0
    #: Lots rattaches a la mission.
    sous_projets: int = 0
    #: Projet dont la mission releve, quand elle est un lot. Il peut etre
    #: archive : le lot en releve toujours, et la carte doit pouvoir y mener.
    parent: Project | None = None
    #: Le dernier message du fil, pour l'annoncer sans ouvrir le panneau.
    derniere_maj: LastUpdate | None = None


@dataclass
class BoardColumn:
    """Une phase et ses cartes, dans l'ordre choisi par l'equipe."""

    statut: ProjectStatus
    cartes: list[BoardCard] = field(default_factory=list)


@dataclass
class Board:
    """Le tableau complet."""

    colonnes: list[BoardColumn]


class GetBoardUseCase:
    """Construit le tableau de bord.

    Toutes les phases sont retournees, meme vides : une colonne absente
    empecherait d'y deposer une carte.

    Les missions archivees en sont ecartees par defaut : le tableau sert a
    piloter ce qui tourne. On les redemande pour faire le point, et tout ce
    qu'une carte annonce — son fil, ses lots — suit alors le meme perimetre.
    """

    def __init__(
        self,
        projects: ProjectRepository,
        entries: EntryRepository,
        users: UserRepository,
        assignees: ProjectAssigneeRepository,
        updates: ProjectUpdateRepository,
    ) -> None:
        self._projects = projects
        self._entries = entries
        self._users = users
        self._assignees = assignees
        self._updates = updates

    async def execute(
        self, today: date | None = None, include_inactive: bool = False
    ) -> Board:
        aujourdhui = today or date.today()

        # Les archivees sont lues meme quand on ne les montre pas : un lot
        # survit a l'archivage de son projet, et sa carte doit continuer a
        # nommer de quoi elle releve.
        toutes = await self._projects.list_all(include_inactive=True)
        par_id = {p.id: p for p in toutes if p.id is not None}
        missions = [
            p for p in toutes if (p.actif or include_inactive) and p.appears_on_board
        ]

        utilisateurs = {u.id: u for u in await self._users.list_all(True)}
        affectations = await self._assignees.list_all(ProjectRole.INTERVENANT)
        commentaires = await self._updates.count_by_project()
        dernieres = await self._updates.latest_by_project()

        def derniere(project_id: int) -> LastUpdate | None:
            maj = dernieres.get(project_id)
            auteur = utilisateurs.get(maj.author_id) if maj else None
            # Un auteur desactive puis efface laisserait un texte anonyme :
            # mieux vaut ne rien annoncer que de le signer d'un blanc.
            return LastUpdate(update=maj, author=auteur) if maj and auteur else None

        nb_lots: dict[int, int] = {}
        for mission in missions:
            if mission.parent_id is not None:
                nb_lots[mission.parent_id] = nb_lots.get(mission.parent_id, 0) + 1

        colonnes = [BoardColumn(statut=statut) for statut in ProjectStatus]
        par_statut = {colonne.statut: colonne for colonne in colonnes}

        # Le libelle departage les rangs egaux : les missions anterieures au
        # tableau partagent toutes la position 0, et leur ordre serait sinon
        # arbitraire d'un chargement a l'autre.
        for mission in sorted(missions, key=lambda p: (p.position, p.label)):
            if mission.statut is None or mission.id is None:
                continue
            saisies = await self._entries.list_for_project(mission.id)

            consomme = round(
                sum(float(e.valeur) for e in saisies if not e.is_forecast(aujourdhui)),
                2,
            )

            # Les intervenants ne se deduisent pas des saisies : une mission peut
            # tourner des semaines sans en recevoir une seule, puis reclamer une
            # journee sur un bug. Ce que le tableau montre, c'est qui s'en occupe
            # ces jours-ci, declare a la main et defait de meme.
            intervenants = sorted(
                affectations.get(mission.id, []),
                key=lambda uid: (
                    utilisateurs[uid].display_name if uid in utilisateurs else ""
                ),
            )

            par_statut[mission.statut].cartes.append(
                BoardCard(
                    project=mission,
                    consomme_j=consomme,
                    intervenants=[
                        utilisateurs[uid] for uid in intervenants if uid in utilisateurs
                    ],
                    commentaires=commentaires.get(mission.id, 0),
                    derniere_maj=derniere(mission.id),
                    sous_projets=nb_lots.get(mission.id, 0),
                    parent=(
                        par_id.get(mission.parent_id)
                        if mission.parent_id is not None
                        else None
                    ),
                )
            )

        return Board(colonnes=colonnes)
