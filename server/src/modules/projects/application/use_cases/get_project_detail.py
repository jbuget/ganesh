"""Gathers everything one wants to read about a mission."""

from dataclasses import dataclass
from datetime import date

from src.modules.entries.domain.repositories.entry_repository import EntryRepository
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
from src.modules.projects.domain.services.hierarchy import with_resolved_category
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.enums.department import Department
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


@dataclass
class Contribution:
    """What one person declared on the mission."""

    user: User
    days: float
    #: Days per month, most recent first. A month is named by its 1st day.
    by_month: list[tuple[date, float]]


@dataclass
class ProjectDetail:
    """The full sheet of a mission."""

    project: Project
    departments: list[Department]
    links: list[ProjectLink]
    phases_reached: dict[ProjectStatus, date]
    leads: list[User]
    contributors: list[User]
    consumed_days: float
    #: Time declared by each person, largest contributor first.
    contributions: list[Contribution]
    #: Work packages attached to the mission, in alphabetical order.
    sub_projects: list[Project]
    #: The project a work package belongs to. A project has none.
    parent: Project | None = None


class GetProjectDetailUseCase:
    """Reads a mission and everything attached to it."""

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
            raise EntityNotFoundError("The mission cannot be found.")

        # A work package has no axis of its own: it is read on its project.
        parent = (
            await self._projects.get_by_id(mission.parent_id)
            if mission.parent_id is not None
            else None
        )

        users = {u.id: u for u in await self._users.list_all(True)}

        async def people(role: ProjectRole) -> list[User]:
            ids = await self._assignees.list_for_project(project_id, role)
            known = [users[uid] for uid in ids if uid in users]
            return sorted(known, key=lambda u: u.label)

        entries = await self._entries.list_for_project(project_id)

        # Time per person tells who really carried the mission, which the list
        # of contributors alone does not: someone may have spent days on it
        # without being assigned to it today.
        by_person: dict[int, float] = {}
        by_month: dict[int, dict[date, float]] = {}
        for entry in entries:
            by_person[entry.user_id] = round(
                by_person.get(entry.user_id, 0.0) + float(entry.value), 2
            )
            month = entry.day.replace(day=1)
            person_months = by_month.setdefault(entry.user_id, {})
            person_months[month] = round(
                person_months.get(month, 0.0) + float(entry.value), 2
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
            project=with_resolved_category(mission, parent),
            departments=await self._details.list_departments(project_id),
            links=await self._details.list_links(project_id),
            phases_reached=await self._details.list_phases_reached(project_id),
            leads=await people(ProjectRole.LEAD),
            contributors=await people(ProjectRole.CONTRIBUTOR),
            consumed_days=round(sum(float(e.value) for e in entries), 2),
            contributions=contributions,
            sub_projects=sorted(
                (
                    with_resolved_category(work_package, mission)
                    for work_package in await self._projects.list_children(project_id)
                ),
                key=lambda work_package: work_package.label.lower(),
            ),
            parent=parent,
        )
