"""Cutting a mission into the trades its days are booked under."""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.application.dtos.activity_dto import (
    ArchiveActivityCommand,
    CreateActivityCommand,
    UpdateActivityCommand,
)
from src.modules.projects.domain.entities.activity import Activity
from src.modules.projects.domain.repositories.activity_repository import (
    ActivityRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.services.estimates import ensure_the_trade_is_free
from src.shared.exceptions.domain_exceptions import EntityNotFoundError, ValidationError


class CreateActivityUseCase:
    """Cuts a new trade into a mission."""

    def __init__(
        self,
        projects: ProjectRepository,
        activities: ActivityRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._projects = projects
        self._activities = activities
        self._audit_logs = audit_logs

    async def execute(self, command: CreateActivityCommand) -> Activity:
        mission = await self._projects.get_by_id(command.project_id)
        if mission is None:
            raise EntityNotFoundError("The mission cannot be found.")
        # Off-project work is declared on directly: absences carry neither
        # estimate nor trade, and cutting them up would buy nothing.
        if mission.is_off_project:
            raise ValidationError(
                f"« {mission.label} » is off-project work: it carries no activity."
            )

        ensure_the_trade_is_free(
            await self._activities.list_for_project(command.project_id),
            command.nature,
        )

        activity = await self._activities.add(
            Activity(
                id=None,
                project_id=command.project_id,
                label=command.label,
                nature=command.nature,
                estimated_days=command.estimated_days,
            )
        )
        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.ACTIVITY_CREATE,
                actor_id=command.actor_id,
                project_id=command.project_id,
                new_value=activity.label,
                payload={"activity_id": activity.id, "nature": activity.nature},
            )
        )
        return activity


class UpdateActivityUseCase:
    """Changes what an activity says, one field at a time."""

    def __init__(
        self,
        activities: ActivityRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._activities = activities
        self._audit_logs = audit_logs

    async def execute(self, command: UpdateActivityCommand) -> Activity:
        activity = await self._activities.get_by_id(command.activity_id)
        if activity is None:
            raise EntityNotFoundError("The activity cannot be found.")

        before = (activity.label, activity.nature, activity.estimated_days)

        if command.label is not None:
            activity.label = command.label
        if command.sets_nature:
            # Checked before the change, not after: the trade it is leaving
            # would otherwise read as taken by itself.
            ensure_the_trade_is_free(
                await self._activities.list_for_project(activity.project_id),
                command.nature,
                moving=activity.id,
            )
            activity.nature = command.nature
        if command.sets_estimated_days:
            activity.estimated_days = command.estimated_days

        # Re-run the entity's own rules: a label blanked or a negative
        # estimate must be refused here as it is at creation.
        activity.__post_init__()

        after = (activity.label, activity.nature, activity.estimated_days)
        if before == after:
            return activity

        saved = await self._activities.update(activity)
        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.ACTIVITY_UPDATE,
                actor_id=command.actor_id,
                project_id=saved.project_id,
                old_value=_said(before),
                new_value=_said(after),
                payload={"activity_id": saved.id},
            )
        )
        return saved


class ArchiveActivityUseCase:
    """Takes an activity out of what a month can be declared on.

    Days already booked stay readable, exactly as they do when a mission is
    archived: only the list one can still declare on shrinks. Nothing is
    deleted, and the estimate leaves with it — an archived trade is no longer
    part of what the mission has left to spend.
    """

    def __init__(
        self,
        activities: ActivityRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._activities = activities
        self._audit_logs = audit_logs

    async def execute(self, command: ArchiveActivityCommand) -> Activity:
        activity = await self._activities.get_by_id(command.activity_id)
        if activity is None:
            raise EntityNotFoundError("The activity cannot be found.")

        was_active = activity.is_active
        activity.archive()
        saved = await self._activities.update(activity)

        if was_active:
            await self._audit_logs.add(
                AuditLog(
                    action=AuditAction.ACTIVITY_ARCHIVE,
                    actor_id=command.actor_id,
                    project_id=saved.project_id,
                    old_value=saved.label,
                    payload={"activity_id": saved.id},
                )
            )
        return saved


class UnarchiveActivityUseCase:
    """Puts an activity back among what can be declared on."""

    def __init__(
        self,
        activities: ActivityRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._activities = activities
        self._audit_logs = audit_logs

    async def execute(self, command: ArchiveActivityCommand) -> Activity:
        activity = await self._activities.get_by_id(command.activity_id)
        if activity is None:
            raise EntityNotFoundError("The activity cannot be found.")

        was_archived = not activity.is_active
        # Coming back has to find the trade free: another activity may have
        # taken it over while this one was away.
        if was_archived:
            ensure_the_trade_is_free(
                await self._activities.list_for_project(activity.project_id),
                activity.nature,
                moving=activity.id,
            )
        activity.unarchive()
        saved = await self._activities.update(activity)

        if was_archived:
            await self._audit_logs.add(
                AuditLog(
                    action=AuditAction.ACTIVITY_UNARCHIVE,
                    actor_id=command.actor_id,
                    project_id=saved.project_id,
                    new_value=saved.label,
                    payload={"activity_id": saved.id},
                )
            )
        return saved


def _said(state: tuple[str, object, float | None]) -> str:
    """What an activity said, in one line the journal can print."""
    label, nature, estimated = state
    trade = str(nature) if nature is not None else "—"
    days = f"{estimated:g} j" if estimated is not None else "—"
    return f"{label} · {trade} · {days}"
