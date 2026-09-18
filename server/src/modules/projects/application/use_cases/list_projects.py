"""Lists the mission reference list."""

from dataclasses import dataclass, field
from datetime import date

from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.projects.application.dtos.last_update import LastUpdate
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
    """A mission, and what the interface needs to offer its actions."""

    project: Project
    entries: int
    sub_projects: int
    #: Qui repond de la mission, par ordre alphabetique.
    leads: list[User] = field(default_factory=list)
    #: Qui y travaille, par ordre alphabetique.
    contributors: list[User] = field(default_factory=list)
    #: Jours declares, previsionnel exclu.
    delivered_days: float = 0.0
    #: Mises a jour vivantes du fil de suivi.
    comments: int = 0
    #: La derniere d'entre elles, pour annoncer le fil sans l'ouvrir.
    latest_update: LastUpdate | None = None

    @property
    def is_deletable(self) -> bool:
        """A mission that never served may disappear; the others get archived."""
        return self.entries == 0 and self.sub_projects == 0


class ListProjectsUseCase:
    """Returns the missions, active ones by default."""

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
        entries = await self._entries.count_by_project()
        realise = await self._entries.sum_realised_by_project(today or date.today())
        comments = await self._updates.count_by_project()
        dernieres = await self._updates.latest_by_project()

        enfants: dict[int, int] = {}
        for mission in await self._projects.list_all(include_inactive=True):
            if mission.parent_id is not None:
                enfants[mission.parent_id] = enfants.get(mission.parent_id, 0) + 1

        # Les affectations se lisent en deux requetes, pas deux par mission : le
        # referentiel en aligne des dizaines sur un meme ecran.
        users = {u.id: u for u in await self._users.list_all(True)}
        par_role = {role: await self._assignees.list_all(role) for role in ProjectRole}

        def people(project_id: int, role: ProjectRole) -> list[User]:
            connus = [
                users[uid] for uid in par_role[role].get(project_id, []) if uid in users
            ]
            return sorted(connus, key=lambda u: u.display_name)

        def latest(project_id: int) -> LastUpdate | None:
            update = dernieres.get(project_id)
            author = users.get(update.author_id) if update else None
            # Un auteur desactive puis efface laisserait un texte anonyme :
            # mieux vaut ne rien annoncer que de le signer d'un blanc.
            return (
                LastUpdate(update=update, author=author) if update and author else None
            )

        return [
            ListedProject(
                project=mission,
                entries=entries.get(mission.id or 0, 0),
                sub_projects=enfants.get(mission.id or 0, 0),
                leads=people(mission.id or 0, ProjectRole.LEAD),
                contributors=people(mission.id or 0, ProjectRole.CONTRIBUTOR),
                delivered_days=realise.get(mission.id or 0, 0.0),
                comments=comments.get(mission.id or 0, 0),
                latest_update=latest(mission.id or 0),
            )
            for mission in missions
        ]
