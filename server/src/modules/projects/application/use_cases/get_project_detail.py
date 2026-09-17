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
    days: float
    #: Jours par mois, du plus recent au plus ancien. Le mois est son 1er jour.
    by_month: list[tuple[date, float]]


@dataclass
class ProjectDetail:
    """La fiche complete d'une mission."""

    project: Project
    departments: list[Department]
    links: list[ProjectLink]
    phases_reached: dict[ProjectStatus, date]
    leads: list[User]
    contributors: list[User]
    consumed_days: float
    #: Temps declare par chacun, du plus gros contributeur au plus petit.
    contributions: list[Contribution]
    #: Les lots rattaches a la mission, par ordre alphabetique.
    sub_projects: list[Project]


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

        users = {u.id: u for u in await self._users.list_all(True)}

        async def people(role: ProjectRole) -> list[User]:
            ids = await self._assignees.list_for_project(project_id, role)
            connus = [users[uid] for uid in ids if uid in users]
            return sorted(connus, key=lambda u: u.display_name)

        entries = await self._entries.list_for_project(project_id)

        # Le temps par personne dit qui a vraiment porte la mission, ce que la
        # seule liste des intervenants ne raconte pas : quelqu'un peut y avoir
        # passe des jours sans y etre affecte aujourd'hui.
        by_person: dict[int, float] = {}
        by_month: dict[int, dict[date, float]] = {}
        for entry in entries:
            by_person[entry.user_id] = round(
                by_person.get(entry.user_id, 0.0) + float(entry.value), 2
            )
            month = entry.day.replace(day=1)
            mois_de_la_personne = by_month.setdefault(entry.user_id, {})
            mois_de_la_personne[month] = round(
                mois_de_la_personne.get(month, 0.0) + float(entry.value), 2
            )

        contributions = sorted(
            (
                Contribution(
                    user=users[uid],
                    days=days,
                    by_month=sorted(
                        by_month.get(uid, {}).items(),
                        key=lambda item: item[0],
                        reverse=True,
                    ),
                )
                for uid, days in by_person.items()
                if uid in users
            ),
            key=lambda contribution: -contribution.days,
        )

        return ProjectDetail(
            project=mission,
            departments=await self._details.list_departments(project_id),
            links=await self._details.list_links(project_id),
            phases_reached=await self._details.list_phases_reached(project_id),
            leads=await people(ProjectRole.LEAD),
            contributors=await people(ProjectRole.CONTRIBUTOR),
            consumed_days=round(sum(float(e.value) for e in entries), 2),
            contributions=contributions,
            sub_projects=sorted(
                await self._projects.list_children(project_id),
                key=lambda work_package: work_package.label.lower(),
            ),
        )
