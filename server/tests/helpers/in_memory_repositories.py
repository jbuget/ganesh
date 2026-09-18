"""In-memory repositories, to test use cases without a database or mocks.

They implement the same ports as the infrastructure: a use case that passes
here passes in production, persistence aside.
"""

from datetime import date

from src.modules.audit_logs.domain.entities.audit_log import AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.entries.domain.entities.entry import Entry
from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.months.domain.entities.month import Month
from src.modules.months.domain.repositories.month_repository import MonthRepository
from src.modules.projects.domain.entities.project import (
    Department,
    Project,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_link import ProjectLink
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.projects.domain.entities.project_update import ProjectUpdate
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
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository


class InMemoryUserRepository(UserRepository):
    def __init__(self, users: list[User] | None = None) -> None:
        self._users: dict[int, User] = {}
        self._next_id = 1
        #: How many writes it took: the freshness window of the last login can
        #: only be checked by counting what the use case persists.
        self.updates = 0
        for user in users or []:
            self._users[user.id or self._next_id] = user
            self._next_id = max(self._next_id, (user.id or 0) + 1)

    async def get_by_id(self, user_id: int) -> User | None:
        return self._users.get(user_id)

    async def get_by_entra_oid(self, entra_oid: str) -> User | None:
        return next((u for u in self._users.values() if u.entra_oid == entra_oid), None)

    async def get_by_email(self, email: str) -> User | None:
        target = email.strip().lower()
        return next((u for u in self._users.values() if u.email == target), None)

    async def list_all(self, include_inactive: bool = False) -> list[User]:
        return [u for u in self._users.values() if include_inactive or u.is_active]

    async def add(self, user: User) -> User:
        user.id = self._next_id
        self._next_id += 1
        self._users[user.id] = user
        return user

    async def update(self, user: User) -> User:
        self.updates += 1
        if user.id is not None:
            self._users[user.id] = user
        return user


class InMemoryProjectRepository(ProjectRepository):
    def __init__(self, projects: list[Project] | None = None) -> None:
        self._projects: dict[int, Project] = {}
        self._next_id = 1
        for project in projects or []:
            self._projects[project.id or self._next_id] = project
            self._next_id = max(self._next_id, (project.id or 0) + 1)

    async def get_by_id(self, project_id: int) -> Project | None:
        return self._projects.get(project_id)

    async def list_all(self, include_inactive: bool = False) -> list[Project]:
        return [p for p in self._projects.values() if include_inactive or p.is_active]

    async def list_children(self, parent_id: int) -> list[Project]:
        return [p for p in self._projects.values() if p.parent_id == parent_id]

    async def add(self, project: Project) -> Project:
        project.id = self._next_id
        self._next_id += 1
        self._projects[project.id] = project
        return project

    async def update(self, project: Project) -> Project:
        if project.id is not None:
            self._projects[project.id] = project
        return project

    async def delete(self, project_id: int) -> None:
        self._projects.pop(project_id, None)


class InMemoryEntryRepository(EntryRepository):
    def __init__(self, entries: list[Entry] | None = None) -> None:
        self._entries: list[Entry] = list(entries or [])
        self._next_id = 1

    async def get(self, user_id: int, project_id: int, day: date) -> Entry | None:
        return next(
            (
                e
                for e in self._entries
                if e.user_id == user_id and e.project_id == project_id and e.day == day
            ),
            None,
        )

    async def list_for_month(self, user_id: int, month: date) -> list[Entry]:
        return [
            e
            for e in self._entries
            if e.user_id == user_id
            and e.day.year == month.year
            and e.day.month == month.month
        ]

    async def list_for_day(self, user_id: int, day: date) -> list[Entry]:
        return [e for e in self._entries if e.user_id == user_id and e.day == day]

    async def list_for_project(self, project_id: int) -> list[Entry]:
        return [e for e in self._entries if e.project_id == project_id]

    async def count_by_project(self) -> dict[int, int]:
        counts: dict[int, int] = {}
        for entry in self._entries:
            counts[entry.project_id] = counts.get(entry.project_id, 0) + 1
        return counts

    async def sum_realised_by_project(self, today: date) -> dict[int, float]:
        totals: dict[int, float] = {}
        for entry in self._entries:
            if entry.is_forecast(today):
                continue
            totals[entry.project_id] = round(
                totals.get(entry.project_id, 0.0) + float(entry.value), 2
            )
        return totals

    async def upsert(self, entry: Entry) -> Entry:
        existing = await self.get(entry.user_id, entry.project_id, entry.day)
        if existing is not None:
            self._entries.remove(existing)
            entry.id = existing.id
        else:
            entry.id = self._next_id
            self._next_id += 1
        self._entries.append(entry)
        return entry

    async def delete(self, user_id: int, project_id: int, day: date) -> None:
        existing = await self.get(user_id, project_id, day)
        if existing is not None:
            self._entries.remove(existing)


class InMemoryMonthRepository(MonthRepository):
    def __init__(self, months: list[Month] | None = None) -> None:
        self._months: list[Month] = list(months or [])

    async def get(self, user_id: int, month: date) -> Month | None:
        first = month.replace(day=1)
        return next(
            (m for m in self._months if m.user_id == user_id and m.month == first),
            None,
        )

    async def list_for_month(self, month: date) -> list[Month]:
        first = month.replace(day=1)
        return [m for m in self._months if m.month == first]

    async def save(self, month: Month) -> Month:
        existing = await self.get(month.user_id, month.month)
        if existing is not None:
            self._months.remove(existing)
        self._months.append(month)
        return month


class InMemoryAuditLogRepository(AuditLogRepository):
    def __init__(self) -> None:
        self.logs: list[AuditLog] = []

    async def add(self, log: AuditLog) -> AuditLog:
        log.id = len(self.logs) + 1
        self.logs.append(log)
        return log

    async def list_for_user_month(
        self, target_user_id: int, month: date
    ) -> list[AuditLog]:
        first = month.replace(day=1)
        return [
            log
            for log in self.logs
            if log.target_user_id == target_user_id
            and log.day is not None
            and log.day.replace(day=1) == first
        ]

    async def list_for_project(self, project_id: int) -> list[AuditLog]:
        return [log for log in self.logs if log.project_id == project_id]


class InMemoryProjectAssigneeRepository(ProjectAssigneeRepository):
    def __init__(
        self, assignments: dict[tuple[int, ProjectRole], list[int]] | None = None
    ) -> None:
        self._by_project: dict[tuple[int, ProjectRole], list[int]] = assignments or {}

    async def list_for_project(self, project_id: int, role: ProjectRole) -> list[int]:
        return list(self._by_project.get((project_id, role), []))

    async def list_all(self, role: ProjectRole) -> dict[int, list[int]]:
        return {
            pid: list(ids) for (pid, r), ids in self._by_project.items() if r is role
        }

    async def assign(self, project_id: int, user_id: int, role: ProjectRole) -> None:
        members = self._by_project.setdefault((project_id, role), [])
        if user_id not in members:
            members.append(user_id)

    async def unassign(self, project_id: int, user_id: int, role: ProjectRole) -> None:
        members = self._by_project.get((project_id, role))
        if members and user_id in members:
            members.remove(user_id)


class InMemoryProjectDetailRepository(ProjectDetailRepository):
    def __init__(self) -> None:
        self._departments: dict[int, list[Department]] = {}
        self._links: dict[int, list[ProjectLink]] = {}
        self._phases: dict[int, dict[ProjectStatus, date]] = {}
        self._next_link_id = 1

    async def list_departments(self, project_id: int) -> list[Department]:
        return list(self._departments.get(project_id, []))

    async def set_departments(
        self, project_id: int, departments: list[Department]
    ) -> None:
        self._departments[project_id] = list(dict.fromkeys(departments))

    async def list_links(self, project_id: int) -> list[ProjectLink]:
        return list(self._links.get(project_id, []))

    async def add_link(self, link: ProjectLink) -> ProjectLink:
        link.id = self._next_link_id
        self._next_link_id += 1
        self._links.setdefault(link.project_id, []).append(link)
        return link

    async def remove_link(self, link_id: int) -> None:
        for links in self._links.values():
            for link in list(links):
                if link.id == link_id:
                    links.remove(link)

    async def list_phases_reached(self, project_id: int) -> dict[ProjectStatus, date]:
        return dict(self._phases.get(project_id, {}))

    async def mark_phase_reached(
        self, project_id: int, status: ProjectStatus, reached_at: date
    ) -> None:
        self._phases.setdefault(project_id, {}).setdefault(status, reached_at)


class InMemoryProjectUpdateRepository(ProjectUpdateRepository):
    def __init__(self) -> None:
        self._updates: list[ProjectUpdate] = []
        self._next_id = 1

    async def get(self, update_id: int) -> ProjectUpdate | None:
        return next((u for u in self._updates if u.id == update_id), None)

    async def list_for_project(self, project_id: int) -> list[ProjectUpdate]:
        thread = [u for u in self._updates if u.project_id == project_id]
        return sorted(thread, key=lambda u: (u.published_at, u.id or 0), reverse=True)

    async def add(self, update: ProjectUpdate) -> ProjectUpdate:
        update.id = self._next_id
        self._next_id += 1
        self._updates.append(update)
        return update

    async def count_by_project(self) -> dict[int, int]:
        counts: dict[int, int] = {}
        for update in self._updates:
            if update.is_deleted:
                continue
            counts[update.project_id] = counts.get(update.project_id, 0) + 1
        return counts

    async def latest_by_project(self) -> dict[int, ProjectUpdate]:
        latest: dict[int, ProjectUpdate] = {}
        for update in sorted(self._updates, key=lambda u: (u.published_at, u.id or 0)):
            if update.is_deleted:
                continue
            latest[update.project_id] = update
        return latest

    async def update(self, update: ProjectUpdate) -> ProjectUpdate:
        return update
