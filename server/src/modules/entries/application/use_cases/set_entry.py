"""Records the time a user spent on a mission, on a given day."""

from datetime import date

from src.modules.audit_logs.domain.entities.audit_log import AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.entries.application.dtos.set_entry_dto import SetEntryCommand
from src.modules.entries.application.use_cases.timesheet_notice import tell_the_owner
from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.entries.domain.services.entry_rules import (
    ensure_activity_belongs_to_the_mission,
    ensure_day_is_workable,
)
from src.modules.months.domain.entities.month import Month
from src.modules.months.domain.repositories.month_repository import MonthRepository
from src.modules.months.domain.services.month_rules import ensure_month_is_open
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.projects.domain.entities.activity import Activity
from src.modules.projects.domain.repositories.activity_repository import (
    ActivityRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)


class SetEntryUseCase:
    """Writes an entry, once the month is known to accept it."""

    def __init__(
        self,
        users: UserRepository,
        projects: ProjectRepository,
        activities: ActivityRepository,
        entries: EntryRepository,
        months: MonthRepository,
        audit_logs: AuditLogRepository,
        notifications: NotificationDelivery,
    ) -> None:
        self._users = users
        self._projects = projects
        self._activities = activities
        self._entries = entries
        self._months = months
        self._audit_logs = audit_logs
        self._notifications = notifications

    async def execute(self, command: SetEntryCommand) -> Entry:
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("The user cannot be found.")
        if not actor.can_edit_open_months():
            raise ForbiddenActionError("A deactivated user can no longer enter time.")

        if await self._users.get_by_id(command.target_user_id) is None:
            raise EntityNotFoundError("The target user cannot be found.")

        project = await self._projects.get_by_id(command.project_id)
        if project is None:
            raise EntityNotFoundError("The mission cannot be found.")

        activity = await self._read_activity(command.activity_id)

        # Domain invariants, checked before any write.
        ensure_activity_belongs_to_the_mission(project, activity)
        ensure_day_is_workable(command.day)
        value = DayValue(command.value)

        month = await self._ensure_open_month(command.target_user_id, command.day)

        previous = await self._entries.get(
            command.target_user_id,
            command.project_id,
            command.activity_id,
            command.day,
        )
        entry = await self._entries.upsert(
            Entry(
                id=previous.id if previous else None,
                user_id=command.target_user_id,
                project_id=command.project_id,
                activity_id=command.activity_id,
                day=command.day,
                value=value,
                status_at_entry=project.status,
            )
        )

        await self._audit_logs.add(
            AuditLog.entry_set(
                actor_id=command.actor_id,
                target_user_id=command.target_user_id,
                project_id=command.project_id,
                day=command.day,
                old_value=float(previous.value) if previous else None,
                new_value=float(value),
            )
        )
        await tell_the_owner(
            self._notifications,
            actor_id=command.actor_id,
            owner_id=command.target_user_id,
            day=command.day,
        )
        await self._months.save(month)
        return entry

    async def _read_activity(self, activity_id: int | None) -> Activity | None:
        """The activity named, or nothing when none was named.

        An id naming no activity is refused here rather than read as « none »:
        the two mean opposite things, and taking one for the other would book
        a day against a mission whose activity had just been withdrawn.
        """
        if activity_id is None:
            return None

        activity = await self._activities.get_by_id(activity_id)
        if activity is None:
            raise EntityNotFoundError("The activity cannot be found.")
        return activity

    async def _ensure_open_month(self, user_id: int, day: date) -> Month:
        """The month the entry lands on, opened on the fly if it is the first."""
        month = await self._months.get(user_id, day)
        ensure_month_is_open(month)
        return month or Month(user_id=user_id, month=day)
