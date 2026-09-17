"""Rassemble tout ce qu'on veut lire sur une mission."""

from dataclasses import dataclass
from datetime import date

from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.projects.domain.entities.project import (
    Department,
    Project,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_link import ProjectLink
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.projects.domain.repositories.project_assignee_repository import (
    ProjectAssigneeRepository,
)
from src.modules.projects.domain.repositories.project_detail_repository import (
    ProjectDetailRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


@dataclass
class Contribution:
    """Ce qu'une personne a declare sur la mission."""

    user: User
    jours: float
    #: Jours par mois, du plus recent au plus ancien. Le mois est son 1er jour.
    par_mois: list[tuple[date, float]]


@dataclass
class ProjectDetail:
    """La fiche complete d'une mission."""

    project: Project
    departements: list[Department]
    liens: list[ProjectLink]
    phases_atteintes: dict[ProjectStatus, date]
    referents: list[User]
    intervenants: list[User]
    consomme_j: float
    #: Temps declare par chacun, du plus gros contributeur au plus petit.
    contributions: list[Contribution]
    #: Les lots rattaches a la mission, par ordre alphabetique.
    sous_projets: list[Project]


class GetProjectDetailUseCase:
    """Lit une mission et tout ce qui s'y rattache."""

    def __init__(
        self,
        projects: ProjectRepository,
        details: ProjectDetailRepository,
        assignees: ProjectAssigneeRepository,
        entries: EntryRepository,
        users: UserRepository,
    ) -> None:
        self._projects = projects
        self._details = details
        self._assignees = assignees
        self._entries = entries
        self._users = users

    async def execute(self, project_id: int) -> ProjectDetail:
        mission = await self._projects.get_by_id(project_id)
        if mission is None:
            raise EntityNotFoundError("Mission inconnue.")

        utilisateurs = {u.id: u for u in await self._users.list_all(True)}

        async def personnes(role: ProjectRole) -> list[User]:
            ids = await self._assignees.list_for_project(project_id, role)
            connus = [utilisateurs[uid] for uid in ids if uid in utilisateurs]
            return sorted(connus, key=lambda u: u.display_name)

        saisies = await self._entries.list_for_project(project_id)

        # Le temps par personne dit qui a vraiment porte la mission, ce que la
        # seule liste des intervenants ne raconte pas : quelqu'un peut y avoir
        # passe des jours sans y etre affecte aujourd'hui.
        par_personne: dict[int, float] = {}
        par_mois: dict[int, dict[date, float]] = {}
        for saisie in saisies:
            par_personne[saisie.user_id] = round(
                par_personne.get(saisie.user_id, 0.0) + float(saisie.valeur), 2
            )
            mois = saisie.jour.replace(day=1)
            mois_de_la_personne = par_mois.setdefault(saisie.user_id, {})
            mois_de_la_personne[mois] = round(
                mois_de_la_personne.get(mois, 0.0) + float(saisie.valeur), 2
            )

        contributions = sorted(
            (
                Contribution(
                    user=utilisateurs[uid],
                    jours=jours,
                    par_mois=sorted(
                        par_mois.get(uid, {}).items(),
                        key=lambda item: item[0],
                        reverse=True,
                    ),
                )
                for uid, jours in par_personne.items()
                if uid in utilisateurs
            ),
            key=lambda contribution: -contribution.jours,
        )

        return ProjectDetail(
            project=mission,
            departements=await self._details.list_departments(project_id),
            liens=await self._details.list_links(project_id),
            phases_atteintes=await self._details.list_phases_reached(project_id),
            referents=await personnes(ProjectRole.REFERENT),
            intervenants=await personnes(ProjectRole.INTERVENANT),
            consomme_j=round(sum(float(e.valeur) for e in saisies), 2),
            contributions=contributions,
            sous_projets=sorted(
                await self._projects.list_children(project_id),
                key=lambda lot: lot.label.lower(),
            ),
        )
