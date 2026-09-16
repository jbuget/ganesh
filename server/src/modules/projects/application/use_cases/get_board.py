"""Assemble le tableau de bord des projets, par phase."""

from dataclasses import dataclass, field
from datetime import date

from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.projects.domain.entities.project import Project, ProjectStatus
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository


@dataclass
class BoardCard:
    """Une carte du tableau : la mission et ce qu'on veut lire dessus."""

    project: Project
    consomme_j: float
    collaborateurs: list[User]


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
    """

    def __init__(
        self,
        projects: ProjectRepository,
        entries: EntryRepository,
        users: UserRepository,
    ) -> None:
        self._projects = projects
        self._entries = entries
        self._users = users

    async def execute(self, today: date | None = None) -> Board:
        aujourdhui = today or date.today()
        missions = [
            p
            for p in await self._projects.list_all(include_inactive=False)
            if p.appears_on_board
        ]
        utilisateurs = {u.id: u for u in await self._users.list_all(True)}

        colonnes = [BoardColumn(statut=statut) for statut in ProjectStatus]
        par_statut = {colonne.statut: colonne for colonne in colonnes}

        # Le libelle departage les rangs egaux : les missions anterieures au
        # tableau partagent toutes la position 0, et leur ordre serait sinon
        # arbitraire d'un chargement a l'autre.
        for mission in sorted(missions, key=lambda p: (p.position, p.label)):
            if mission.statut is None or mission.id is None:
                continue
            saisies = await self._entries.list_for_project(mission.id)

            # Le previsionnel ne compte pas dans le consomme, mais il dit deja
            # qui travaillera sur la mission : l'information est utile au
            # pilotage, on la garde pour les collaborateurs.
            consomme = round(
                sum(float(e.valeur) for e in saisies if not e.is_forecast(aujourdhui)),
                2,
            )
            intervenants = sorted(
                {e.user_id for e in saisies},
                key=lambda uid: (
                    utilisateurs[uid].display_name if uid in utilisateurs else ""
                ),
            )

            par_statut[mission.statut].cartes.append(
                BoardCard(
                    project=mission,
                    consomme_j=consomme,
                    collaborateurs=[
                        utilisateurs[uid] for uid in intervenants if uid in utilisateurs
                    ],
                )
            )

        return Board(colonnes=colonnes)
