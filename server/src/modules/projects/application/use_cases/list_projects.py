"""Lists the mission reference list."""

from dataclasses import dataclass, field
from datetime import date, timedelta

from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.projects.application.dtos.last_update import LastUpdate
from src.modules.projects.domain.entities.project import Project, ProjectStatus
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
from src.modules.projects.domain.repositories.project_update_repository import (
    ProjectUpdateRepository,
)
from src.modules.projects.domain.services.deletion import can_be_deleted
from src.modules.projects.domain.services.hierarchy import with_resolved_category
from src.modules.projects.domain.services.project_cost import (
    NO_COST,
    RUN_WINDOW_DAYS,
    ProjectCost,
    roll_up,
    split_delivered,
)
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository


@dataclass
class ListedProject:
    """A mission, and what the interface needs to offer its actions."""

    project: Project
    entries: int
    sub_projects: int
    #: Who answers for the mission, in alphabetical order.
    leads: list[User] = field(default_factory=list)
    #: Who works on it, in alphabetical order.
    contributors: list[User] = field(default_factory=list)
    #: Days declared, forecast excluded.
    delivered_days: float = 0.0
    #: What the mission cost, the build kept apart from the run.
    cost: ProjectCost = NO_COST
    #: The same count, plus what its work packages cost.
    tree_cost: ProjectCost = NO_COST
    #: The useful addresses attached to the mission, in the order they were added.
    links: list[ProjectLink] = field(default_factory=list)
    #: Live updates in the follow-up thread.
    comments: int = 0
    #: The latest of them, to announce the thread without opening it.
    latest_update: LastUpdate | None = None

    @property
    def is_deletable(self) -> bool:
        """A mission that never served may disappear; the others get archived."""
        return can_be_deleted(self.project, self.entries, self.sub_projects)


class ListProjectsUseCase:
    """Returns the missions, active ones by default."""

    def __init__(
        self,
        projects: ProjectRepository,
        entries: EntryRepository,
        assignees: ProjectAssigneeRepository,
        users: UserRepository,
        updates: ProjectUpdateRepository,
        details: ProjectDetailRepository,
    ) -> None:
        self._projects = projects
        self._entries = entries
        self._assignees = assignees
        self._users = users
        self._updates = updates
        self._details = details

    async def execute(
        self, include_inactive: bool = False, today: date | None = None
    ) -> list[ListedProject]:
        day = today or date.today()
        missions = await self._projects.list_all(include_inactive=include_inactive)
        entries = await self._entries.count_by_project()
        delivered = await self._entries.sum_realised_by_project(day)
        comments = await self._updates.count_by_project()
        latest_by_project = await self._updates.latest_by_project()
        links = await self._details.list_links_by_project()

        # The count is read over the whole tree, work packages a filter left
        # out included: what an evolution cost is still the cost of the service.
        all_missions = await self._projects.list_all(include_inactive=True)
        children: dict[int, int] = {}
        for mission in all_missions:
            if mission.parent_id is not None:
                children[mission.parent_id] = children.get(mission.parent_id, 0) + 1

        costs = await self._costs(all_missions, day)

        # Archived projects included: a work package outlives the archiving of
        # its project, and goes on reading with the axis of that project.
        by_id = {m.id: m for m in all_missions if m.id is not None}

        # Assignments are read in two queries, not two per mission: the
        # reference list lines up dozens of them on a single screen.
        users = {u.id: u for u in await self._users.list_all(True)}
        by_role = {role: await self._assignees.list_all(role) for role in ProjectRole}

        def people(project_id: int, role: ProjectRole) -> list[User]:
            known = [
                users[uid] for uid in by_role[role].get(project_id, []) if uid in users
            ]
            return sorted(known, key=lambda u: u.label)

        def latest(project_id: int) -> LastUpdate | None:
            update = latest_by_project.get(project_id)
            author = users.get(update.author_id) if update else None
            # An author deactivated then deleted would leave an anonymous
            # text: better to announce nothing than to sign it with a blank.
            return (
                LastUpdate(update=update, author=author) if update and author else None
            )

        return [
            ListedProject(
                project=with_resolved_category(
                    mission, by_id.get(mission.parent_id or 0)
                ),
                entries=entries.get(mission.id or 0, 0),
                sub_projects=children.get(mission.id or 0, 0),
                leads=people(mission.id or 0, ProjectRole.LEAD),
                contributors=people(mission.id or 0, ProjectRole.CONTRIBUTOR),
                delivered_days=delivered.get(mission.id or 0, 0.0),
                links=links.get(mission.id or 0, []),
                cost=costs.own.get(mission.id or 0, NO_COST),
                tree_cost=costs.tree.get(mission.id or 0, NO_COST),
                comments=comments.get(mission.id or 0, 0),
                latest_update=latest(mission.id or 0),
            )
            for mission in missions
        ]

    async def _costs(self, missions: list[Project], today: date) -> "MissionCosts":
        """What each mission cost, on its own and with its work packages.

        Read in three queries whatever the number of missions: the phases the
        days were spent in, the same over the recent window, and the day each
        mission went live.
        """
        by_status = await self._entries.sum_realised_by_project_and_status(today)
        recent = await self._entries.sum_realised_by_project_and_status(
            today, since=today - timedelta(days=RUN_WINDOW_DAYS)
        )
        live_since = await self._details.list_dates_reached(ProjectStatus.OPERATIONS)

        own = {
            mission.id: split_delivered(
                by_status.get(mission.id or 0, {}),
                recent.get(mission.id or 0, {}),
                estimated_days=mission.estimated_days,
                in_run_since=live_since.get(mission.id or 0),
            )
            for mission in missions
            if mission.id is not None
        }
        parents = {
            mission.id: mission.parent_id
            for mission in missions
            if mission.id is not None
        }
        return MissionCosts(own=own, tree=roll_up(own, parents))


@dataclass(frozen=True)
class MissionCosts:
    """The cost of every mission, read alone and read as a tree."""

    own: dict[int, ProjectCost]
    tree: dict[int, ProjectCost]
