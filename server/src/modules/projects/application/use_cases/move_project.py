"""Moves a card on the board."""

from datetime import date

from src.modules.audit_logs.domain.entities.audit_log import AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.application.dtos.project_dto import MoveProjectCommand
from src.modules.projects.domain.entities.project import Project, ProjectStatus
from src.modules.projects.domain.repositories.project_detail_repository import (
    ProjectDetailRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.domain.services.board_ordering import reorder_column
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError, ValidationError


class MoveProjectUseCase:
    """Changes a card's phase, its rank, or both.

    A drag and drop always produces both: the column it lands in and the rank
    wanted. Handling them together avoids two concurrent writes for a single
    gesture.
    """

    def __init__(
        self,
        users: UserRepository,
        projects: ProjectRepository,
        details: ProjectDetailRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._users = users
        self._projects = projects
        self._details = details
        self._audit_logs = audit_logs

    async def execute(
        self, command: MoveProjectCommand, today: date | None = None
    ) -> Project:
        if await self._users.get_by_id(command.actor_id) is None:
            raise EntityNotFoundError("Utilisateur inconnu.")

        mission = await self._projects.get_by_id(command.project_id)
        if mission is None or mission.id is None:
            raise EntityNotFoundError("Mission inconnue.")
        if not mission.appears_on_board:
            raise ValidationError("Off-project work does not appear on the board.")

        ancienne_phase = mission.status
        missions = await self._projects.list_all(include_inactive=False)

        mission.status = command.status
        # Dragging a card crosses a phase just as a change from the reference
        # list does: the date is recorded on both sides.
        await self._details.mark_phase_reached(
            command.project_id, command.status, today or date.today()
        )

        # The drop is reasoned about by id, never by object identity:
        # `get_by_id` and `list_all` return two distinct instances of the same
        # row, and writing the old one would overwrite the rank just set on the
        # new one.
        destination = [
            p
            for p in missions
            if p.status is command.status and p.appears_on_board and p.id != mission.id
        ]
        destination.append(mission)
        reorder_column(destination, deplacee=mission, vers=command.position)

        # The column left behind would keep a gap where the card used to be.
        if ancienne_phase is not command.status:
            origin = [
                p
                for p in missions
                if p.status is ancienne_phase
                and p.appears_on_board
                and p.id != mission.id
            ]
            for position, restante in enumerate(
                sorted(origin, key=lambda p: p.position)
            ):
                restante.position = position
            for restante in origin:
                await self._projects.update(restante)

        for rangee in destination:
            await self._projects.update(rangee)

        if ancienne_phase is not command.status:
            await self._audit_logs.add(
                AuditLog.project_status_change(
                    actor_id=command.actor_id,
                    project_id=mission.id,
                    old_status=ancienne_phase.value if ancienne_phase else None,
                    new_status=command.status.value,
                )
            )
        return mission


__all__ = ["MoveProjectUseCase", "ProjectStatus"]
