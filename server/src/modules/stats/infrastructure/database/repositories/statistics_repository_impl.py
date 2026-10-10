"""SQLAlchemy implementation of the StatisticsRepository port."""

from datetime import date

from sqlalchemy import and_, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, aliased
from sqlalchemy.sql.elements import ColumnElement

from src.modules.api_keys.infrastructure.database.models.api_key_models import (
    ApiKeyModel,
)
from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.audit_logs.infrastructure.database.models.audit_log_model import (
    AuditLogModel,
)
from src.modules.calendar.domain.entities.period import Period
from src.modules.entries.infrastructure.database.models.entry_model import EntryModel
from src.modules.months.domain.entities.month import MonthState
from src.modules.months.infrastructure.database.models.month_model import MonthModel
from src.modules.moods.infrastructure.database.models.mood_model import MoodModel
from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.infrastructure.database.models.notification_model import (
    NotificationModel,
)
from src.modules.projects.domain.entities.project import (
    ProjectCategory,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.projects.infrastructure.database.models.activity_model import (
    ActivityModel,
)
from src.modules.projects.infrastructure.database.models.project_assignee_model import (
    ProjectAssigneeModel,
)
from src.modules.projects.infrastructure.database.models.project_model import (
    ProjectModel,
)
from src.modules.projects.infrastructure.database.models.project_update_model import (
    ProjectUpdateModel,
)
from src.modules.projects.infrastructure.database.models.update_comment_model import (
    UpdateCommentModel,
)
from src.modules.projects.infrastructure.database.models.update_reaction_model import (
    UpdateReactionModel,
)
from src.modules.requests.domain.entities.request import RequestState
from src.modules.requests.infrastructure.database.models.request_model import (
    RequestModel,
)
from src.modules.stats.domain.entities.surface_usage import Surface, Tally, Trace
from src.modules.stats.domain.repositories.statistics_repository import (
    StatisticsRepository,
)
from src.shared.enums.work_nature import WorkNature


class SqlStatisticsRepository(StatisticsRepository):
    """Counts the window straight in the database.

    Every figure is an aggregate: the dashboard never walks a list of entries
    to work out a percentage, however small the team is today.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _within(self, period: Period) -> ColumnElement[bool]:
        return EntryModel.day.between(period.start, period.end)

    async def declared_days(self, period: Period, user_ids: list[int]) -> float:
        total = await self._session.scalar(
            select(func.coalesce(func.sum(EntryModel.value), 0.0)).where(
                self._within(period), EntryModel.user_id.in_(user_ids)
            )
        )
        return float(total or 0.0)

    async def contributor_ids(self, period: Period) -> set[int]:
        rows = await self._session.execute(
            select(EntryModel.user_id).where(self._within(period)).distinct()
        )
        return {user_id for (user_id,) in rows.all()}

    async def entry_delays(self, period: Period) -> list[int]:
        """How long each entry of the window waited before being written.

        Read from the audit log rather than from the entries: `updated_at`
        moves on every correction, while the log keeps the moment the day was
        first declared.
        """
        rows = await self._session.execute(
            select(AuditLogModel.at, AuditLogModel.day).where(
                and_(
                    AuditLogModel.action == AuditAction.ENTRY_SET,
                    AuditLogModel.day.is_not(None),
                    func.date(AuditLogModel.at).between(period.start, period.end),
                )
            )
        )
        return [max(0, (at.date() - day).days) for at, day in rows.all()]

    async def days_by_kind(self, period: Period) -> dict[ProjectKind, float]:
        rows = await self._session.execute(
            select(ProjectModel.kind, func.sum(EntryModel.value))
            .join(ProjectModel, ProjectModel.id == EntryModel.project_id)
            .where(self._within(period))
            .group_by(ProjectModel.kind)
        )
        return {kind: float(total) for kind, total in rows.all()}

    async def days_by_status(self, period: Period) -> dict[ProjectStatus, float]:
        rows = await self._session.execute(
            select(EntryModel.status_at_entry, func.sum(EntryModel.value))
            .where(and_(self._within(period), EntryModel.status_at_entry.is_not(None)))
            .group_by(EntryModel.status_at_entry)
        )
        return {status: float(total) for status, total in rows.all()}

    async def days_by_category(
        self, period: Period
    ) -> dict[ProjectCategory | None, float]:
        """Time per strategic axis, work packages counted with their parent.

        A work package carries no axis of its own: the axis is the parent
        project's, and leaving it out would hide part of what was spent on it.
        """
        parent = func.coalesce(ProjectModel.parent_id, ProjectModel.id)
        owner = select(ProjectModel.id, ProjectModel.category).subquery()
        rows = await self._session.execute(
            select(owner.c.category, func.sum(EntryModel.value))
            .select_from(EntryModel)
            .join(ProjectModel, ProjectModel.id == EntryModel.project_id)
            .join(owner, owner.c.id == parent)
            .where(self._within(period))
            .group_by(owner.c.category)
        )
        return {category: float(total) for category, total in rows.all()}

    async def days_by_nature(self, period: Period) -> dict[WorkNature | None, float]:
        """Project time per trade, the days with no activity read as none.

        An outer join: what the reprise took over carries no activity at all,
        and an inner one would drop exactly the days nobody ever placed.
        """
        rows = await self._session.execute(
            select(ActivityModel.nature, func.sum(EntryModel.value))
            .select_from(EntryModel)
            .join(ProjectModel, ProjectModel.id == EntryModel.project_id)
            .outerjoin(ActivityModel, ActivityModel.id == EntryModel.activity_id)
            .where(
                and_(
                    self._within(period),
                    ProjectModel.kind != ProjectKind.OFF_PROJECT,
                )
            )
            .group_by(ActivityModel.nature)
        )
        return {nature: float(total) for nature, total in rows.all()}

    async def top_missions(
        self, period: Period, limit: int
    ) -> list[tuple[int, str, float]]:
        total = func.sum(EntryModel.value)
        rows = await self._session.execute(
            select(ProjectModel.id, ProjectModel.label, total)
            .join(EntryModel, EntryModel.project_id == ProjectModel.id)
            .where(self._within(period))
            .group_by(ProjectModel.id, ProjectModel.label)
            .order_by(total.desc(), ProjectModel.label)
            .limit(limit)
        )
        return [(id_, label, float(days)) for id_, label, days in rows.all()]

    async def validated_months(self, months: list[date], user_ids: list[int]) -> int:
        if not months or not user_ids:
            return 0
        count = await self._session.scalar(
            select(func.count())
            .select_from(MonthModel)
            .where(
                and_(
                    MonthModel.month.in_(months),
                    MonthModel.user_id.in_(user_ids),
                    MonthModel.state == MonthState.VALIDATED,
                )
            )
        )
        return int(count or 0)

    async def active_missions(self) -> int:
        count = await self._session.scalar(
            select(func.count())
            .select_from(ProjectModel)
            .where(ProjectModel.is_active.is_(True))
        )
        return int(count or 0)

    async def active_missions_with_time(self, period: Period) -> int:
        count = await self._session.scalar(
            select(func.count(func.distinct(EntryModel.project_id)))
            .select_from(EntryModel)
            .join(ProjectModel, ProjectModel.id == EntryModel.project_id)
            .where(and_(self._within(period), ProjectModel.is_active.is_(True)))
        )
        return int(count or 0)

    async def missions_created(self, period: Period) -> int:
        """Missions added over the window, read from the trace of their birth.

        A project carries no creation date of its own; the audit log does, and
        it is the record that matters anyway.
        """
        count = await self._session.scalar(
            select(func.count())
            .select_from(AuditLogModel)
            .where(
                and_(
                    AuditLogModel.action == AuditAction.PROJECT_CREATE,
                    func.date(AuditLogModel.at).between(period.start, period.end),
                )
            )
        )
        return int(count or 0)

    def _bookable(self) -> list[ColumnElement[bool]]:
        """Active missions that are booked against through activities."""
        return [
            ProjectModel.is_active.is_(True),
            ProjectModel.kind != ProjectKind.OFF_PROJECT,
            ~self._has_active_package(),
        ]

    @staticmethod
    def _has_active_package() -> ColumnElement[bool]:
        package = aliased(ProjectModel)
        return exists().where(
            package.parent_id == ProjectModel.id, package.is_active.is_(True)
        )

    async def missions_without_activity(self) -> int:
        has_trade = exists().where(
            ActivityModel.project_id == ProjectModel.id,
            ActivityModel.is_active.is_(True),
        )
        return await self._count_missions(*self._bookable(), ~has_trade)

    async def missions_unbudgeted(self) -> int:
        has_unbudgeted_trade = exists().where(
            ActivityModel.project_id == ProjectModel.id,
            ActivityModel.is_active.is_(True),
            ActivityModel.estimated_days.is_(None),
        )
        return await self._count_missions(*self._bookable(), has_unbudgeted_trade)

    async def followed_missions(self) -> int:
        return await self._count_missions(
            ProjectModel.is_active.is_(True), ProjectModel.is_followed.is_(True)
        )

    async def published_missions(self) -> int:
        return await self._count_missions(
            ProjectModel.is_active.is_(True), ProjectModel.is_published.is_(True)
        )

    async def _count_missions(self, *conditions: ColumnElement[bool]) -> int:
        count = await self._session.scalar(
            select(func.count()).select_from(ProjectModel).where(*conditions)
        )
        return int(count or 0)

    async def requests_submitted(self, period: Period) -> int:
        return await self._count_requests(
            func.date(RequestModel.submitted_at).between(period.start, period.end)
        )

    async def requests_decided(self, period: Period) -> dict[RequestState, int]:
        rows = await self._session.execute(
            select(RequestModel.state, func.count())
            .where(func.date(RequestModel.decided_at).between(period.start, period.end))
            .group_by(RequestModel.state)
        )
        return {state: int(count) for state, count in rows.all()}

    async def requests_converted(self, period: Period) -> int:
        return await self._count_requests(
            func.date(RequestModel.converted_at).between(period.start, period.end)
        )

    async def requests_waiting_since(self) -> list[date]:
        rows = await self._session.execute(
            select(func.date(RequestModel.submitted_at)).where(
                RequestModel.state == RequestState.SUBMITTED
            )
        )
        return sorted(day for (day,) in rows.all())

    async def _count_requests(self, *conditions: ColumnElement[bool]) -> int:
        count = await self._session.scalar(
            select(func.count()).select_from(RequestModel).where(*conditions)
        )
        return int(count or 0)

    @staticmethod
    def _active_project() -> list[ColumnElement[bool]]:
        return [
            ProjectModel.is_active.is_(True),
            ProjectModel.kind == ProjectKind.PROJECT,
        ]

    async def active_projects(self) -> int:
        return await self._count_missions(*self._active_project())

    async def projects_without_role(self, role: ProjectRole) -> int:
        held = exists().where(
            ProjectAssigneeModel.project_id == ProjectModel.id,
            ProjectAssigneeModel.role == role,
        )
        return await self._count_missions(*self._active_project(), ~held)

    async def followed_last_news(self) -> list[date | None]:
        rows = await self._session.execute(
            select(func.max(func.date(ProjectUpdateModel.published_at)))
            .select_from(ProjectModel)
            .outerjoin(
                ProjectUpdateModel,
                and_(
                    ProjectUpdateModel.project_id == ProjectModel.id,
                    ProjectUpdateModel.deleted_at.is_(None),
                ),
            )
            .where(
                ProjectModel.is_active.is_(True),
                ProjectModel.is_followed.is_(True),
            )
            .group_by(ProjectModel.id)
        )
        return [day for (day,) in rows.all()]

    def _posted_within(self, period: Period) -> list[ColumnElement[bool]]:
        return [
            ProjectUpdateModel.deleted_at.is_(None),
            func.date(ProjectUpdateModel.published_at).between(
                period.start, period.end
            ),
        ]

    async def updates_posted(self, period: Period) -> int:
        count = await self._session.scalar(
            select(func.count())
            .select_from(ProjectUpdateModel)
            .where(*self._posted_within(period))
        )
        return int(count or 0)

    async def updates_answered(self, period: Period) -> int:
        replied = exists().where(
            UpdateCommentModel.update_id == ProjectUpdateModel.id,
            UpdateCommentModel.author_id != ProjectUpdateModel.author_id,
            UpdateCommentModel.deleted_at.is_(None),
        )
        reacted = exists().where(
            UpdateReactionModel.update_id == ProjectUpdateModel.id,
            UpdateReactionModel.user_id != ProjectUpdateModel.author_id,
        )
        count = await self._session.scalar(
            select(func.count())
            .select_from(ProjectUpdateModel)
            .where(*self._posted_within(period), replied | reacted)
        )
        return int(count or 0)

    async def notification_reading(
        self, period: Period
    ) -> dict[NotificationKind, tuple[int, int]]:
        rows = await self._session.execute(
            select(
                NotificationModel.kind,
                func.count(),
                func.count(NotificationModel.read_at),
            )
            .where(func.date(NotificationModel.at).between(period.start, period.end))
            .group_by(NotificationModel.kind)
        )
        return {kind: (int(sent), int(read)) for kind, sent, read in rows.all()}

    async def unread_notifications(self, older_than: date | None = None) -> int:
        conditions: list[ColumnElement[bool]] = [NotificationModel.read_at.is_(None)]
        if older_than is not None:
            conditions.append(func.date(NotificationModel.at) < older_than)
        count = await self._session.scalar(
            select(func.count()).select_from(NotificationModel).where(*conditions)
        )
        return int(count or 0)

    async def surface_traces(self, period: Period) -> list[Trace]:
        rows = await self._session.execute(
            select(AuditLogModel.action, AuditLogModel.actor_id, func.count())
            .where(func.date(AuditLogModel.at).between(period.start, period.end))
            .group_by(AuditLogModel.action, AuditLogModel.actor_id)
        )
        return [
            Trace(action=action, actor_id=actor_id, gestures=int(gestures))
            for action, actor_id, gestures in rows.all()
        ]

    async def gestures_by_day(self, period: Period) -> dict[date, int]:
        day = func.date(AuditLogModel.at)
        rows = await self._session.execute(
            select(day, func.count())
            .where(day.between(period.start, period.end))
            .group_by(day)
        )
        return {gestured_on: int(gestures) for gestured_on, gestures in rows.all()}

    async def last_gestures(self) -> dict[AuditAction, date]:
        rows = await self._session.execute(
            select(
                AuditLogModel.action, func.max(func.date(AuditLogModel.at))
            ).group_by(AuditLogModel.action)
        )
        return dict(rows.all())

    async def unlogged_tallies(self, period: Period) -> dict[Surface, Tally]:
        return {
            Surface.MOOD: await self._moods_posted(period),
            Surface.NOTIFICATIONS: await self._notifications_read(period),
            Surface.MACHINE_ACCESS: await self._keys_used(period),
        }

    async def last_unlogged_use(self) -> dict[Surface, date]:
        latest = {
            Surface.MOOD: func.max(func.date(MoodModel.created_at)),
            Surface.NOTIFICATIONS: func.max(func.date(NotificationModel.read_at)),
            Surface.MACHINE_ACCESS: func.max(func.date(ApiKeyModel.last_used_at)),
        }
        days = {
            surface: await self._session.scalar(select(column))
            for surface, column in latest.items()
        }
        return {surface: day for surface, day in days.items() if day is not None}

    async def _moods_posted(self, period: Period) -> Tally:
        """Who said how their days felt. How they felt is read nowhere here.

        Counted on the day it was posted rather than on the day it is about,
        as freshness already counts the entries *written* over the window: a
        mood posted on Monday for last Friday is somebody using the screen on
        Monday, and dating it to Friday would drop the use out of the window
        that saw it.
        """
        return await self._tally(
            MoodModel.user_id,
            func.date(MoodModel.created_at).between(period.start, period.end),
        )

    async def _notifications_read(self, period: Period) -> Tally:
        """Notifications opened. A read is a trace, and this one is recorded."""
        return await self._tally(
            NotificationModel.recipient_id,
            func.date(NotificationModel.read_at).between(period.start, period.end),
        )

    async def _keys_used(self, period: Period) -> Tally:
        """Keys that served, counted through the people who answer for them.

        Only the last call of each key is stored, so this counts keys that
        were used at least once and never how often. The screen says so.
        """
        return await self._tally(
            ApiKeyModel.owner_id,
            func.date(ApiKeyModel.last_used_at).between(period.start, period.end),
        )

    async def _tally(
        self, person: InstrumentedAttribute[int], within: ColumnElement[bool]
    ) -> Tally:
        row = await self._session.execute(
            select(func.count(func.distinct(person)), func.count()).where(within)
        )
        people, gestures = row.one()
        return Tally(people=int(people or 0), gestures=int(gestures or 0))
