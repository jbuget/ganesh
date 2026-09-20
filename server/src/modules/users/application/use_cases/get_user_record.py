"""Gathers what the register holds on one teammate.

Nothing here is computed: the reading lives in `user_record`, and this puts a
name on every mission id it hands back.
"""

from calendar import monthrange
from datetime import date

from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.months.domain.repositories.month_repository import MonthRepository
from src.modules.projects.domain.entities.project import Project, ProjectKind
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.projects.domain.repositories.project_assignee_repository import (
    ProjectAssigneeRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.application.dtos.user_record_dto import (
    DeclaredMission,
    DeclaredWindow,
    GetUserRecordQuery,
    RecordedMission,
    UserRecord,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.modules.users.domain.services.user_record import (
    days_by_project,
    declaration_window,
    month_fillings,
    months_looked_back,
)
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from src.shared.utils import clock


def _last_day_of(month: date) -> date:
    return month.replace(day=monthrange(month.year, month.month)[1])


class GetUserRecordUseCase:
    """Reads one teammate's missions, declared time and months."""

    def __init__(
        self,
        users: UserRepository,
        projects: ProjectRepository,
        assignees: ProjectAssigneeRepository,
        entries: EntryRepository,
        months: MonthRepository,
    ) -> None:
        self._users = users
        self._projects = projects
        self._assignees = assignees
        self._entries = entries
        self._months = months

    def _missions_held(
        self, roles: dict[int, list[ProjectRole]], known: dict[int, Project]
    ) -> list[RecordedMission]:
        """The missions one is attached to, in the alphabet's order.

        An archived mission is left out: the section says what somebody works
        on, and a mission out of the reference list is not something one still
        books against. What time it already received is read below, where the
        past belongs.
        """
        held = []
        for project_id, roles_held in roles.items():
            project = known.get(project_id)
            if project is None or not project.is_active:
                continue
            held.append(
                RecordedMission(
                    project_id=project_id,
                    label=project.label,
                    status=project.status,
                    is_lead=ProjectRole.LEAD in roles_held,
                )
            )
        return sorted(held, key=lambda mission: mission.label)

    async def execute(self, query: GetUserRecordQuery) -> UserRecord:
        if await self._users.get_by_id(query.user_id) is None:
            raise EntityNotFoundError("The user cannot be found.")

        today = query.today or clock.today()
        span = months_looked_back(today)
        # One read covering everything: the months looked back, and the month
        # running right to its end, so that days posted ahead are counted as
        # the forecast they are.
        entries = await self._entries.list_for_user_between(
            query.user_id, span[-1], _last_day_of(span[0])
        )

        # The whole reference list at once, archived missions included: the
        # panel names a dozen of them, and one read per name would make them
        # arrive one after the other.
        known = {
            project.id: project
            for project in await self._projects.list_all(include_inactive=True)
            if project.id is not None
        }

        since, until = declaration_window(today)
        declared = [
            DeclaredMission(
                project_id=line.project_id,
                label=project.label,
                days=line.days,
                is_off_project=project.kind is ProjectKind.OFF_PROJECT,
            )
            for line in days_by_project(entries, since, until)
            if (project := known.get(line.project_id)) is not None
        ]

        return UserRecord(
            user_id=query.user_id,
            missions=self._missions_held(
                await self._assignees.list_for_user(query.user_id), known
            ),
            declared=DeclaredWindow(
                since=since,
                until=until,
                days=round(sum(line.days for line in declared), 2),
                missions=declared,
            ),
            months=month_fillings(
                entries=entries,
                states=await self._months.list_for_user(query.user_id, span[-1]),
                today=today,
            ),
        )
