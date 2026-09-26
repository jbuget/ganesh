"""Posting, moving and withdrawing the dates a mission answers for."""

from datetime import date

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.application.dtos.milestone_dto import (
    CreateMilestoneCommand,
    DeleteMilestoneCommand,
    UpdateMilestoneCommand,
)
from src.modules.projects.domain.entities.milestone import Milestone
from src.modules.projects.domain.repositories.milestone_repository import (
    MilestoneRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.shared.exceptions.domain_exceptions import EntityNotFoundError, ValidationError


class CreateMilestoneUseCase:
    """Posts a date on a mission."""

    def __init__(
        self,
        projects: ProjectRepository,
        milestones: MilestoneRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._projects = projects
        self._milestones = milestones
        self._audit_logs = audit_logs

    async def execute(self, command: CreateMilestoneCommand) -> Milestone:
        mission = await self._projects.get_by_id(command.project_id)
        if mission is None:
            raise EntityNotFoundError("The mission cannot be found.")
        # Off-project work steers nothing and is announced to nobody: an
        # absence has no day it is answerable for.
        if mission.is_off_project:
            raise ValidationError(
                f"« {mission.label} » is off-project work: it carries no milestone."
            )

        milestone = await self._milestones.add(
            Milestone(
                id=None,
                project_id=command.project_id,
                label=command.label,
                expected_on=command.expected_on,
                reached_on=command.reached_on,
            )
        )
        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.MILESTONE_CREATE,
                actor_id=command.actor_id,
                project_id=command.project_id,
                new_value=milestone.label,
                payload={"milestone_id": milestone.id},
            )
        )
        return milestone


class UpdateMilestoneUseCase:
    """Changes what a milestone says, one field at a time."""

    def __init__(
        self,
        milestones: MilestoneRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._milestones = milestones
        self._audit_logs = audit_logs

    async def execute(self, command: UpdateMilestoneCommand) -> Milestone:
        milestone = await self._milestones.get_by_id(command.milestone_id)
        if milestone is None:
            raise EntityNotFoundError("The milestone cannot be found.")

        before = (milestone.label, milestone.expected_on, milestone.reached_on)

        if command.label is not None:
            milestone.label = command.label
        if command.expected_on is not None:
            milestone.expected_on = command.expected_on
        if command.sets_reached_on:
            milestone.reached_on = command.reached_on

        # Re-run the entity's own rules: a label blanked or a day still to
        # come must be refused here as it is when the date is first posted.
        milestone.__post_init__()

        after = (milestone.label, milestone.expected_on, milestone.reached_on)
        if before == after:
            return milestone

        saved = await self._milestones.update(milestone)
        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.MILESTONE_UPDATE,
                actor_id=command.actor_id,
                project_id=saved.project_id,
                old_value=_said(before),
                new_value=_said(after),
                payload={"milestone_id": saved.id},
            )
        )
        return saved


class DeleteMilestoneUseCase:
    """Withdraws a date from a mission.

    Deleted outright, unlike an activity: nothing is ever booked against a
    milestone, so its going empties no month and takes no declared day with
    it. A date posted by mistake simply leaves.
    """

    def __init__(
        self,
        milestones: MilestoneRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._milestones = milestones
        self._audit_logs = audit_logs

    async def execute(self, command: DeleteMilestoneCommand) -> None:
        milestone = await self._milestones.get_by_id(command.milestone_id)
        if milestone is None:
            raise EntityNotFoundError("The milestone cannot be found.")

        await self._milestones.delete(command.milestone_id)
        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.MILESTONE_DELETE,
                actor_id=command.actor_id,
                project_id=milestone.project_id,
                old_value=milestone.label,
                payload={"milestone_id": milestone.id},
            )
        )


def _said(state: tuple[str, date, date | None]) -> str:
    """What a milestone said, in one line the journal can print."""
    label, expected, reached = state
    crossed = f"atteint le {reached:%d/%m/%Y}" if reached else "non atteint"
    return f"{label} · prévu le {expected:%d/%m/%Y} · {crossed}"


class ListProjectMilestonesUseCase:
    """The dates a mission answers for, in the order they happen."""

    def __init__(self, milestones: MilestoneRepository) -> None:
        self._milestones = milestones

    async def execute(self, project_id: int) -> list[Milestone]:
        return await self._milestones.list_for_project(project_id)
