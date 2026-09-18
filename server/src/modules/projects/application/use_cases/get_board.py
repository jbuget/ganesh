"""Assembles the project board, phase by phase."""

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
from src.modules.projects.domain.services.project_cost import split_delivered
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository


@dataclass
class BoardCard:
    """A board card: the mission, and what one wants to read on it."""

    project: Project
    consumed_days: float
    contributors: list[User]
    #: Days spent building it, the run left apart: it is the only count the
    #: estimate covers.
    build_days: float = 0.0
    #: Live updates in the follow-up thread.
    comments: int = 0
    #: Work packages attached to the mission.
    sub_projects: int = 0
    #: The project the mission belongs to, when it is a work package. It may
    #: be archived: the package still belongs to it, and the card must lead
    #: there.
    parent: Project | None = None
    #: The latest message of the thread, to announce it without opening the panel.
    latest_update: LastUpdate | None = None


@dataclass
class BoardColumn:
    """A phase and its cards, in the order the team chose."""

    status: ProjectStatus
    cards: list[BoardCard] = field(default_factory=list)


@dataclass
class Board:
    """The whole board."""

    columns: list[BoardColumn]


class GetBoardUseCase:
    """Builds the board.

    Every phase comes back, even empty ones: a missing column would leave
    nowhere to drop a card.

    Archived missions are left out by default: the board is there to steer what
    is running. They are asked for when taking stock, and everything a card
    announces — its thread, its work packages — then follows the same scope.
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
        today = today or date.today()

        # Archived missions are read even when they are not shown: a work
        # package outlives the archiving of its project, and its card must go
        # on naming what it belongs to.
        all_missions = await self._projects.list_all(include_inactive=True)
        by_id = {p.id: p for p in all_missions if p.id is not None}
        missions = [
            p
            for p in all_missions
            if (p.is_active or include_inactive) and p.appears_on_board
        ]

        users = {u.id: u for u in await self._users.list_all(True)}
        assignments = await self._assignees.list_all(ProjectRole.CONTRIBUTOR)
        comments = await self._updates.count_by_project()
        latest_by_project = await self._updates.latest_by_project()

        def latest(project_id: int) -> LastUpdate | None:
            update = latest_by_project.get(project_id)
            author = users.get(update.author_id) if update else None
            # An author deactivated then deleted would leave an anonymous
            # text: better to announce nothing than to sign it with a blank.
            return (
                LastUpdate(update=update, author=author) if update and author else None
            )

        work_package_counts: dict[int, int] = {}
        for mission in missions:
            if mission.parent_id is not None:
                work_package_counts[mission.parent_id] = (
                    work_package_counts.get(mission.parent_id, 0) + 1
                )

        columns = [BoardColumn(status=status) for status in ProjectStatus]
        by_status = {column.status: column for column in columns}

        # The label breaks ties between equal ranks: missions that predate the
        # board all share position 0, and their order would otherwise be
        # arbitrary from one load to the next.
        for mission in sorted(missions, key=lambda p: (p.position, p.label)):
            if mission.status is None or mission.id is None:
                continue
            entries = await self._entries.list_for_project(mission.id)

            delivered = [e for e in entries if not e.is_forecast(today)]
            consumed = round(sum(float(e.value) for e in delivered), 2)

            # The estimate only covers the construction: comparing the whole
            # total to it would declare every maintained service late.
            by_phase: dict[ProjectStatus | None, float] = {}
            for entry in delivered:
                by_phase[entry.status_at_entry] = by_phase.get(
                    entry.status_at_entry, 0.0
                ) + float(entry.value)
            cost = split_delivered(by_phase)

            # Contributors are not deduced from entries: a mission can run for
            # weeks without a single one, then claim a day on a bug. What the
            # board shows is who is on it these days, declared by hand and
            # undone the same way.
            contributors = sorted(
                assignments.get(mission.id, []),
                key=lambda uid: (users[uid].display_name if uid in users else ""),
            )

            by_status[mission.status].cards.append(
                BoardCard(
                    project=mission,
                    consumed_days=consumed,
                    build_days=cost.build_days,
                    contributors=[users[uid] for uid in contributors if uid in users],
                    comments=comments.get(mission.id, 0),
                    latest_update=latest(mission.id),
                    sub_projects=work_package_counts.get(mission.id, 0),
                    parent=(
                        by_id.get(mission.parent_id)
                        if mission.parent_id is not None
                        else None
                    ),
                )
            )

        return Board(columns=columns)
