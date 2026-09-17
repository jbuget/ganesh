"""Liste le referentiel des missions."""

from dataclasses import dataclass, field
from datetime import date

from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.projects.domain.entities.project import Project
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
class ListedProject:
    """Une mission et ce que l'interface doit savoir pour proposer ses actions."""

    project: Project
    saisies: int
    sous_projets: int
    #: Qui repond de la mission, par ordre alphabetique.
    referents: list[User] = field(default_factory=list)
    #: Qui y travaille, par ordre alphabetique.
    intervenants: list[User] = field(default_factory=list)
    #: Jours declares, previsionnel exclu.
    realise_j: float = 0.0
    #: Mises a jour vivantes du fil de suivi.
    commentaires: int = 0

    @property
    def is_deletable(self) -> bool:
        """Une mission qui n'a jamais servi peut disparaitre ; les autres s'archivent."""
        return self.saisies == 0 and self.sous_projets == 0


class ListProjectsUseCase:
    """Retourne les missions, actives par defaut."""

    def __init__(
        self,
        projects: ProjectRepository,
        entries: EntryRepository,
        assignees: ProjectAssigneeRepository,
        users: UserRepository,
        updates: ProjectUpdateRepository,
    ) -> None:
        self._projects = projects
        self._entries = entries
        self._assignees = assignees
        self._users = users
        self._updates = updates

    async def execute(
        self, include_inactive: bool = False, today: date | None = None
    ) -> list[ListedProject]:
        missions = await self._projects.list_all(include_inactive=include_inactive)
        saisies = await self._entries.count_by_project()
        realise = await self._entries.sum_realised_by_project(today or date.today())
        commentaires = await self._updates.count_by_project()

        enfants: dict[int, int] = {}
        for mission in await self._projects.list_all(include_inactive=True):
            if mission.parent_id is not None:
                enfants[mission.parent_id] = enfants.get(mission.parent_id, 0) + 1

        # Les affectations se lisent en deux requetes, pas deux par mission : le
        # referentiel en aligne des dizaines sur un meme ecran.
        utilisateurs = {u.id: u for u in await self._users.list_all(True)}
        par_role = {role: await self._assignees.list_all(role) for role in ProjectRole}

        def personnes(project_id: int, role: ProjectRole) -> list[User]:
            connus = [
                utilisateurs[uid]
                for uid in par_role[role].get(project_id, [])
                if uid in utilisateurs
            ]
            return sorted(connus, key=lambda u: u.display_name)

        return [
            ListedProject(
                project=mission,
                saisies=saisies.get(mission.id or 0, 0),
                sous_projets=enfants.get(mission.id or 0, 0),
                referents=personnes(mission.id or 0, ProjectRole.REFERENT),
                intervenants=personnes(mission.id or 0, ProjectRole.INTERVENANT),
                realise_j=realise.get(mission.id or 0, 0.0),
                commentaires=commentaires.get(mission.id or 0, 0),
            )
            for mission in missions
        ]
