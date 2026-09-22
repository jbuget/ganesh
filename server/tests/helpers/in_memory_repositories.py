"""In-memory repositories, to test use cases without a database or mocks.

They implement the same ports as the infrastructure: a use case that passes
here passes in production, persistence aside.
"""

from collections.abc import Collection
from dataclasses import replace
from datetime import date, datetime

from src.modules.activity.domain.repositories.activity_repository import (
    ActivityRepository,
    DeclaredDays,
    MissionRecord,
)
from src.modules.api_keys.domain.entities.api_key import ApiKey
from src.modules.api_keys.domain.repositories.api_key_repository import ApiKeyRepository
from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.calendar.domain.entities.period import Period
from src.modules.entries.domain.entities.entry import Entry
from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.entries.domain.repositories.user_mission_repository import (
    UserMissionRepository,
)
from src.modules.gazette.domain.entities.digest import Digest, DigestVersion
from src.modules.gazette.domain.repositories.digest_repository import DigestRepository
from src.modules.months.domain.entities.month import Month
from src.modules.months.domain.repositories.month_repository import MonthRepository
from src.modules.months.domain.services.month_period import first_day_of
from src.modules.moods.domain.entities.mood import Mood
from src.modules.moods.domain.repositories.mood_repository import MoodRepository
from src.modules.notifications.domain.entities.notification import (
    Notification,
    NotificationKind,
)
from src.modules.notifications.domain.repositories.notification_repository import (
    NotificationRepository,
)
from src.modules.planning.domain.entities.simulation import Simulation
from src.modules.planning.domain.repositories.simulation_repository import (
    SimulationRepository,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_attachment import ProjectAttachment
from src.modules.projects.domain.entities.project_link import ProjectLink
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.projects.domain.repositories.attachment_store import AttachmentStore
from src.modules.projects.domain.repositories.project_assignee_repository import (
    ProjectAssigneeRepository,
)
from src.modules.projects.domain.repositories.project_attachment_repository import (
    ProjectAttachmentRepository,
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
from src.modules.requests.domain.entities.request import Request
from src.modules.requests.domain.repositories.request_repository import (
    RequestRepository,
)
from src.modules.stats.domain.entities.surface_usage import Surface, Tally, Trace
from src.modules.stats.domain.repositories.statistics_repository import (
    StatisticsRepository,
)
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.enums.department import Department, in_declared_order
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


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

    async def get_by_slug(self, slug: str) -> Project | None:
        return next((p for p in self._projects.values() if p.slug == slug), None)

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


class InMemoryApiKeyRepository(ApiKeyRepository):
    def __init__(self, keys: list[ApiKey] | None = None) -> None:
        self._keys: dict[int, ApiKey] = {}
        self._next_id = 1
        for key in keys or []:
            self._keys[key.id or self._next_id] = key
            self._next_id = max(self._next_id, (key.id or 0) + 1)

    async def add(self, key: ApiKey) -> ApiKey:
        key.id = self._next_id
        self._next_id += 1
        self._keys[key.id] = key
        return key

    async def get_by_id(self, key_id: int) -> ApiKey | None:
        return self._keys.get(key_id)

    async def get_by_public_id(self, public_id: str) -> ApiKey | None:
        return next((k for k in self._keys.values() if k.public_id == public_id), None)

    async def list_all(self) -> list[ApiKey]:
        return sorted(self._keys.values(), key=lambda k: k.created_at, reverse=True)

    async def update(self, key: ApiKey) -> None:
        if key.id is not None:
            self._keys[key.id] = key

    async def record_use(self, key_id: int, used_at: datetime) -> None:
        key = self._keys.get(key_id)
        if key is not None:
            key.last_used_at = used_at


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

    async def list_for_user_between(
        self, user_id: int, start: date, end: date
    ) -> list[Entry]:
        return sorted(
            (
                e
                for e in self._entries
                if e.user_id == user_id and start <= e.day <= end
            ),
            key=lambda e: e.day,
        )

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

    async def sum_realised_by_project_and_status(
        self, today: date, since: date | None = None
    ) -> dict[int, dict[ProjectStatus | None, float]]:
        sums: dict[int, dict[ProjectStatus | None, float]] = {}
        for entry in self._entries:
            if entry.is_forecast(today) or (since is not None and entry.day < since):
                continue
            by_status = sums.setdefault(entry.project_id, {})
            by_status[entry.status_at_entry] = round(
                by_status.get(entry.status_at_entry, 0.0) + float(entry.value), 2
            )
        return sums

    async def span_by_project(self) -> dict[int, tuple[date, date]]:
        spans: dict[int, tuple[date, date]] = {}
        for entry in self._entries:
            first, last = spans.get(entry.project_id, (entry.day, entry.day))
            spans[entry.project_id] = (min(first, entry.day), max(last, entry.day))
        return spans

    async def sum_forecast_by_project(self, today: date) -> dict[int, float]:
        totals: dict[int, float] = {}
        for entry in self._entries:
            if not entry.is_forecast(today):
                continue
            totals[entry.project_id] = round(
                totals.get(entry.project_id, 0.0) + float(entry.value), 2
            )
        return totals

    async def sum_by_user_and_day(
        self, start: date, end: date
    ) -> dict[int, dict[date, float]]:
        diaries: dict[int, dict[date, float]] = {}
        for entry in self._entries:
            if entry.day < start or entry.day > end:
                continue
            diary = diaries.setdefault(entry.user_id, {})
            diary[entry.day] = round(diary.get(entry.day, 0.0) + float(entry.value), 2)
        return diaries

    async def list_over(self, start: date, end: date) -> list[Entry]:
        return sorted(
            (e for e in self._entries if start <= e.day <= end),
            key=lambda e: (e.day, e.user_id, e.project_id),
        )

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

    async def list_for_user(self, user_id: int, since: date) -> list[Month]:
        first = first_day_of(since)
        return sorted(
            (m for m in self._months if m.user_id == user_id and m.month >= first),
            key=lambda m: m.month,
        )

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

    def _for_user_month(self, target_user_id: int, month: date) -> list[AuditLog]:
        first = month.replace(day=1)
        return sorted(
            (
                log
                for log in self.logs
                if log.target_user_id == target_user_id
                and log.day is not None
                and log.day.replace(day=1) == first
            ),
            key=lambda log: (log.at, log.id or 0),
            reverse=True,
        )

    async def list_for_user_month(
        self, target_user_id: int, month: date, limit: int, offset: int
    ) -> list[AuditLog]:
        return self._for_user_month(target_user_id, month)[offset : offset + limit]

    async def count_for_user_month(self, target_user_id: int, month: date) -> int:
        return len(self._for_user_month(target_user_id, month))

    def _for_project(self, project_id: int) -> list[AuditLog]:
        return sorted(
            (log for log in self.logs if log.project_id == project_id),
            key=lambda log: (log.at, log.id or 0),
            reverse=True,
        )

    async def list_for_project(
        self, project_id: int, limit: int, offset: int
    ) -> list[AuditLog]:
        return self._for_project(project_id)[offset : offset + limit]

    async def count_for_project(self, project_id: int) -> int:
        return len(self._for_project(project_id))

    def _all(self, since: datetime | None) -> list[AuditLog]:
        return sorted(
            (log for log in self.logs if since is None or log.at >= since),
            key=lambda log: (log.at, log.id or 0),
            reverse=True,
        )

    async def list_all(
        self, limit: int, offset: int, since: datetime | None = None
    ) -> list[AuditLog]:
        return self._all(since)[offset : offset + limit]

    async def count_all(self, since: datetime | None = None) -> int:
        return len(self._all(since))

    async def list_between(
        self,
        start: datetime,
        end: datetime,
        actions: Collection[AuditAction] | None = None,
    ) -> list[AuditLog]:
        return sorted(
            (
                log
                for log in self.logs
                if start <= log.at <= end and (actions is None or log.action in actions)
            ),
            key=lambda log: (log.at, log.id or 0),
        )

    async def last_touch_per_project(
        self, actions: Collection[AuditAction], limit: int
    ) -> list[AuditLog]:
        latest: dict[int, AuditLog] = {}
        for log in sorted(self.logs, key=lambda log: (log.at, log.id or 0)):
            if log.project_id is not None and log.action in actions:
                latest[log.project_id] = log
        return sorted(
            latest.values(), key=lambda log: (log.at, log.id or 0), reverse=True
        )[:limit]


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

    async def list_for_user(self, user_id: int) -> dict[int, list[ProjectRole]]:
        by_project: dict[int, list[ProjectRole]] = {}
        for (project_id, role), members in self._by_project.items():
            if user_id in members:
                by_project.setdefault(project_id, []).append(role)
        return by_project

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
        self._stack: dict[int, list[str]] = {}
        self._tags: dict[int, list[str]] = {}
        self._dependencies: dict[int, list[int]] = {}
        self._next_link_id = 1

    async def list_departments(self, project_id: int) -> list[Department]:
        return in_declared_order(self._departments.get(project_id, []))

    async def list_departments_by_project(self) -> dict[int, list[Department]]:
        return {
            project_id: in_declared_order(departments)
            for project_id, departments in self._departments.items()
            if departments
        }

    async def set_departments(
        self, project_id: int, departments: list[Department]
    ) -> None:
        self._departments[project_id] = list(dict.fromkeys(departments))

    async def list_links(self, project_id: int) -> list[ProjectLink]:
        return list(self._links.get(project_id, []))

    async def list_links_by_project(self) -> dict[int, list[ProjectLink]]:
        return {
            project_id: list(links)
            for project_id, links in self._links.items()
            if links
        }

    async def add_link(self, link: ProjectLink) -> ProjectLink:
        link.id = self._next_link_id
        self._next_link_id += 1
        self._links.setdefault(link.project_id, []).append(link)
        return link

    async def get_link(self, link_id: int) -> ProjectLink | None:
        for links in self._links.values():
            for link in links:
                if link.id == link_id:
                    return link
        return None

    async def remove_link(self, link_id: int) -> None:
        for links in self._links.values():
            for link in list(links):
                if link.id == link_id:
                    links.remove(link)

    async def list_phases_reached(self, project_id: int) -> dict[ProjectStatus, date]:
        return dict(self._phases.get(project_id, {}))

    async def list_phases_reached_by_project(
        self,
    ) -> dict[int, dict[ProjectStatus, date]]:
        return {project_id: dict(phases) for project_id, phases in self._phases.items()}

    async def list_dates_reached(self, status: ProjectStatus) -> dict[int, date]:
        return {
            project_id: phases[status]
            for project_id, phases in self._phases.items()
            if status in phases
        }

    async def mark_phase_reached(
        self, project_id: int, status: ProjectStatus, reached_at: date
    ) -> None:
        self._phases.setdefault(project_id, {}).setdefault(status, reached_at)

    async def list_stack(self, project_id: int) -> list[str]:
        return sorted(self._stack.get(project_id, []))

    async def set_stack(self, project_id: int, technologies: list[str]) -> None:
        self._stack[project_id] = list(dict.fromkeys(technologies))

    async def list_tags(self, project_id: int) -> list[str]:
        return sorted(self._tags.get(project_id, []))

    async def set_tags(self, project_id: int, tags: list[str]) -> None:
        self._tags[project_id] = list(dict.fromkeys(tags))

    async def list_dependencies(self, project_id: int) -> list[int]:
        return sorted(self._dependencies.get(project_id, []))

    async def set_dependencies(self, project_id: int, depends_on: list[int]) -> None:
        self._dependencies[project_id] = list(dict.fromkeys(depends_on))


class InMemoryProjectUpdateRepository(ProjectUpdateRepository):
    def __init__(self) -> None:
        self._updates: list[ProjectUpdate] = []
        self._next_id = 1

    async def get(self, update_id: int) -> ProjectUpdate | None:
        return next((u for u in self._updates if u.id == update_id), None)

    async def list_for_project(self, project_id: int) -> list[ProjectUpdate]:
        thread = [u for u in self._updates if u.project_id == project_id]
        return sorted(thread, key=lambda u: (u.published_at, u.id or 0), reverse=True)

    async def authors_for_project(self, project_id: int) -> set[int]:
        return {
            update.author_id
            for update in self._updates
            if update.project_id == project_id
        }

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


class InMemoryProjectAttachmentRepository(ProjectAttachmentRepository):
    def __init__(self) -> None:
        self.attachments: list[ProjectAttachment] = []
        self._next_id = 1

    async def get(self, attachment_id: int) -> ProjectAttachment | None:
        return next((a for a in self.attachments if a.id == attachment_id), None)

    async def list_for_project(self, project_id: int) -> list[ProjectAttachment]:
        held = [a for a in self.attachments if a.project_id == project_id]
        return sorted(held, key=lambda a: (a.uploaded_at, a.id or 0), reverse=True)

    async def keys_for_project(self, project_id: int) -> list[str]:
        return [a.storage_key for a in self.attachments if a.project_id == project_id]

    async def add(self, attachment: ProjectAttachment) -> ProjectAttachment:
        attachment.id = self._next_id
        self._next_id += 1
        self.attachments.append(attachment)
        return attachment

    async def update(self, attachment: ProjectAttachment) -> ProjectAttachment:
        return attachment

    async def remove(self, attachment_id: int) -> None:
        self.attachments = [a for a in self.attachments if a.id != attachment_id]


class InMemoryAttachmentStore(AttachmentStore):
    """The object store, held in a dict.

    What it is asked to do is as much under test as what it holds: a use case
    that writes the register without ever putting the bytes down would pass on
    content alone.
    """

    def __init__(self) -> None:
        self.content: dict[str, bytes] = {}
        self.types: dict[str, str] = {}

    async def put(self, key: str, content: bytes, content_type: str) -> None:
        self.content[key] = content
        self.types[key] = content_type

    async def get(self, key: str) -> bytes:
        if key not in self.content:
            raise EntityNotFoundError("The file cannot be found.")
        return self.content[key]

    async def delete(self, key: str) -> None:
        self.content.pop(key, None)
        self.types.pop(key, None)


class InMemoryActivityRepository(ActivityRepository):
    """What the Synthèse d'activité reads, held in memory.

    Rows are handed in already grouped, as the database would return them:
    the use case is what is under test, not the SQL.
    """

    def __init__(
        self,
        declared: dict[str, list[DeclaredDays]] | None = None,
        missions: list[MissionRecord] | None = None,
    ) -> None:
        #: Rows per window, keyed by « start:end » so that the window before
        #: can be given a different answer from the one on screen.
        self._declared = declared or {}
        self._missions = missions or []

    @staticmethod
    def key(period: Period) -> str:
        return f"{period.start}:{period.end}"

    async def declared_days(self, period: Period) -> list[DeclaredDays]:
        return self._declared.get(self.key(period), [])

    async def missions_touched(self, period: Period) -> list[MissionRecord]:
        return self._missions

    async def days_by_mission(self, period: Period) -> dict[int, float]:
        days: dict[int, float] = {}
        for row in await self.declared_days(period):
            days[row.project_id] = days.get(row.project_id, 0.0) + row.days
        return days


class InMemoryStatisticsRepository(StatisticsRepository):
    """Dashboard figures, handed over rather than counted from a database.

    `declared_by_day` is dated rather than fixed: it is the one figure read
    over two windows, and only real days prove the comparison window is the
    one the use case asked for.
    """

    def __init__(
        self,
        declared_by_day: dict[date, float] | None = None,
        contributors: set[int] | None = None,
        delays: list[int] | None = None,
        by_kind: dict[ProjectKind, float] | None = None,
        by_status: dict[ProjectStatus, float] | None = None,
        by_category: dict[ProjectCategory | None, float] | None = None,
        missions: list[tuple[int, str, float]] | None = None,
        validated_months: int = 0,
        active_missions: int = 0,
        missions_with_time: int = 0,
        created: int = 0,
        traces: dict[date, list[Trace]] | None = None,
        tallies: dict[date, dict[Surface, Tally]] | None = None,
        last_gestures: dict[AuditAction, date] | None = None,
        last_unlogged_use: dict[Surface, date] | None = None,
    ) -> None:
        self._declared_by_day = declared_by_day or {}
        self._contributors = contributors or set()
        self._delays = delays or []
        self._by_kind = by_kind or {}
        self._by_status = by_status or {}
        self._by_category = by_category or {}
        self._missions = missions or []
        self._validated_months = validated_months
        self._active_missions = active_missions
        self._missions_with_time = missions_with_time
        self._created = created
        self._traces = traces or {}
        self._tallies = tallies or {}
        self._last_gestures = last_gestures or {}
        self._last_unlogged_use = last_unlogged_use or {}

    async def declared_days(self, period: Period) -> float:
        return sum(
            value for day, value in self._declared_by_day.items() if period.covers(day)
        )

    async def contributor_ids(self, period: Period) -> set[int]:
        return self._contributors

    async def entry_delays(self, period: Period) -> list[int]:
        return self._delays

    async def days_by_kind(self, period: Period) -> dict[ProjectKind, float]:
        return self._by_kind

    async def days_by_status(self, period: Period) -> dict[ProjectStatus, float]:
        return self._by_status

    async def days_by_category(
        self, period: Period
    ) -> dict[ProjectCategory | None, float]:
        return self._by_category

    async def top_missions(
        self, period: Period, limit: int
    ) -> list[tuple[int, str, float]]:
        return sorted(self._missions, key=lambda mission: -mission[2])[:limit]

    async def validated_months(self, months: list[date], user_ids: list[int]) -> int:
        return self._validated_months

    async def active_missions(self) -> int:
        return self._active_missions

    async def active_missions_with_time(self, period: Period) -> int:
        return self._missions_with_time

    async def missions_created(self, period: Period) -> int:
        return self._created

    async def surface_traces(self, period: Period) -> list[Trace]:
        return [
            trace
            for day, traces in self._traces.items()
            if period.covers(day)
            for trace in traces
        ]

    async def unlogged_tallies(self, period: Period) -> dict[Surface, Tally]:
        # One day per window in a test: a second one covered by the same
        # window simply takes the place of the first.
        covered: dict[Surface, Tally] = {}
        for day, tallies in self._tallies.items():
            if period.covers(day):
                covered.update(tallies)
        return covered

    async def last_gestures(self) -> dict[AuditAction, date]:
        return self._last_gestures

    async def last_unlogged_use(self) -> dict[Surface, date]:
        return self._last_unlogged_use


class InMemorySimulationRepository(SimulationRepository):
    def __init__(self, simulations: list[Simulation] | None = None) -> None:
        self._simulations: dict[int, Simulation] = {}
        self._next_id = 1
        for simulation in simulations or []:
            self._simulations[simulation.id or self._next_id] = simulation
            self._next_id = max(self._next_id, (simulation.id or 0) + 1)

    async def list_all(self) -> list[Simulation]:
        return list(self._simulations.values())

    async def get_by_id(self, simulation_id: int) -> Simulation | None:
        return self._simulations.get(simulation_id)

    async def find_by_name(self, name: str) -> Simulation | None:
        target = name.strip().casefold()
        return next(
            (s for s in self._simulations.values() if s.name.casefold() == target),
            None,
        )

    async def add(self, simulation: Simulation) -> Simulation:
        simulation.id = self._next_id
        self._next_id += 1
        self._simulations[simulation.id] = simulation
        return simulation

    async def update(self, simulation: Simulation) -> Simulation:
        if simulation.id is not None:
            self._simulations[simulation.id] = simulation
        return simulation

    async def delete(self, simulation_id: int) -> None:
        self._simulations.pop(simulation_id, None)


class InMemoryUserMissionRepository(UserMissionRepository):
    def __init__(self, rows: list[tuple[int, int, date]] | None = None) -> None:
        self._rows: set[tuple[int, int, date]] = {
            (user_id, project_id, first_day_of(month))
            for user_id, project_id, month in rows or []
        }

    async def list_for_month(self, user_id: int, month: date) -> list[int]:
        return [
            project_id
            for row_user, project_id, row_month in sorted(self._rows)
            if row_user == user_id and row_month == first_day_of(month)
        ]

    async def add(self, user_id: int, project_id: int, month: date) -> None:
        self._rows.add((user_id, project_id, first_day_of(month)))

    async def remove(self, user_id: int, project_id: int, month: date) -> None:
        self._rows.discard((user_id, project_id, first_day_of(month)))


class InMemoryMoodRepository(MoodRepository):
    def __init__(self, moods: list[Mood] | None = None) -> None:
        self._moods: list[Mood] = list(moods or [])
        self._next_id = 1

    async def get(self, user_id: int, day: date) -> Mood | None:
        return next(
            (
                mood
                for mood in self._moods
                if mood.user_id == user_id and mood.day == day
            ),
            None,
        )

    async def list_between(self, start: date, end: date) -> list[Mood]:
        return [mood for mood in self._moods if start <= mood.day <= end]

    async def list_for_user_between(
        self, user_id: int, start: date, end: date
    ) -> list[Mood]:
        return [
            mood
            for mood in self._moods
            if mood.user_id == user_id and start <= mood.day <= end
        ]

    async def upsert(self, mood: Mood) -> Mood:
        existing = await self.get(mood.user_id, mood.day)
        if existing is None:
            mood.id = self._next_id
            self._next_id += 1
            self._moods.append(mood)
            return mood
        existing.level = mood.level
        return existing

    async def delete(self, user_id: int, day: date) -> None:
        existing = await self.get(user_id, day)
        if existing is not None:
            self._moods.remove(existing)


class InMemoryNotificationRepository(NotificationRepository):
    def __init__(self) -> None:
        self.notifications: list[Notification] = []
        self._next_id = 1

    async def add(self, notification: Notification) -> Notification:
        notification.id = self._next_id
        self._next_id += 1
        self.notifications.append(notification)
        return notification

    async def save(self, notification: Notification) -> None:
        # Held by reference: the entity handed back is the one stored.
        return None

    async def find_open_twin(
        self,
        recipient_id: int,
        kind: NotificationKind,
        actor_id: int,
        day: date | None,
    ) -> Notification | None:
        for notification in self.notifications:
            if (
                notification.recipient_id == recipient_id
                and notification.kind == kind
                and notification.actor_id == actor_id
                and notification.day == day
                and not notification.is_read
            ):
                return notification
        return None

    def _mine(self, recipient_id: int, unread_only: bool) -> list[Notification]:
        return sorted(
            (
                notification
                for notification in self.notifications
                if notification.recipient_id == recipient_id
                and (not unread_only or not notification.is_read)
            ),
            key=lambda notification: (notification.at, notification.id or 0),
            reverse=True,
        )

    async def list_for(
        self, recipient_id: int, unread_only: bool, limit: int, offset: int
    ) -> list[Notification]:
        return self._mine(recipient_id, unread_only)[offset : offset + limit]

    async def count_for(self, recipient_id: int, unread_only: bool) -> int:
        return len(self._mine(recipient_id, unread_only))

    async def set_read_state(
        self,
        recipient_id: int,
        ids: list[int] | None,
        read: bool,
        at: datetime,
    ) -> int:
        touched = 0
        for notification in self.notifications:
            if notification.recipient_id != recipient_id:
                continue
            if ids is not None and notification.id not in ids:
                continue
            if notification.is_read == read:
                continue
            if read:
                notification.mark_read(at)
            else:
                notification.mark_unread()
            touched += 1
        return touched


class InMemoryDigestRepository(DigestRepository):
    def __init__(self) -> None:
        self.digests: list[Digest] = []

    def _for(self, month: date) -> list[Digest]:
        return sorted(
            (digest for digest in self.digests if digest.month == month),
            key=lambda digest: digest.version,
            reverse=True,
        )

    async def get_latest(self, month: date) -> Digest | None:
        found = self._for(month)
        return found[0] if found else None

    async def get_version(self, month: date, version: int) -> Digest | None:
        return next(
            (digest for digest in self._for(month) if digest.version == version),
            None,
        )

    async def list_versions(self, month: date) -> list[DigestVersion]:
        return [
            DigestVersion(
                version=digest.version,
                generated_at=digest.generated_at,
                requested_by=digest.requested_by,
            )
            for digest in self._for(month)
        ]

    async def add(self, digest: Digest) -> Digest:
        stored = replace(digest, id=len(self.digests) + 1)
        self.digests.append(stored)
        return stored


class InMemoryRequestRepository(RequestRepository):
    def __init__(self, requests: list[Request] | None = None) -> None:
        self._requests: dict[int, Request] = {}
        self._next_id = 1
        for request in requests or []:
            self._requests[request.id or self._next_id] = request
            self._next_id = max(self._next_id, (request.id or 0) + 1)

    async def get_by_id(self, request_id: int) -> Request | None:
        return self._requests.get(request_id)

    async def list_for_requester(self, requester_id: int) -> list[Request]:
        return [
            request
            for request in self._requests.values()
            if request.requester_id == requester_id
        ]

    async def list_all(self, include_drafts: bool = False) -> list[Request]:
        return [
            request
            for request in self._requests.values()
            if include_drafts or not request.is_draft
        ]

    async def add(self, request: Request) -> Request:
        request.id = self._next_id
        self._next_id += 1
        self._requests[request.id] = request
        return request

    async def update(self, request: Request) -> Request:
        if request.id is not None:
            self._requests[request.id] = request
        return request

    async def delete(self, request_id: int) -> None:
        self._requests.pop(request_id, None)
