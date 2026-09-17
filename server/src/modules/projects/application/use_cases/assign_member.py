"""Declare ou retire un intervenant sur une mission."""

from src.modules.audit_logs.domain.entities.audit_log import AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.projects.application.dtos.assignment_dto import AssignmentCommand
from src.modules.projects.domain.repositories.project_assignee_repository import (
    ProjectAssigneeRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


class _AssignmentUseCase:
    """Ce que partagent l'ajout et le retrait : verifier avant d'ecrire.

    Affecter quelqu'un n'est pas un acte de gestion : chacun peut dire qui
    s'apprete a intervenir, comme chacun peut deja corriger le mois d'un
    collegue. Seules l'existence de la mission et celle de la personne sont
    verifiees.
    """

    def __init__(
        self,
        users: UserRepository,
        projects: ProjectRepository,
        assignees: ProjectAssigneeRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._users = users
        self._projects = projects
        self._assignees = assignees
        self._audit_logs = audit_logs

    async def _ensure_both_exist(self, command: AssignmentCommand) -> None:
        if await self._projects.get_by_id(command.project_id) is None:
            raise EntityNotFoundError("Mission inconnue.")
        if await self._users.get_by_id(command.member_id) is None:
            raise EntityNotFoundError("Utilisateur inconnu.")


class AssignMemberUseCase(_AssignmentUseCase):
    """Declare qu'une personne intervient, ou va intervenir, sur une mission."""

    async def execute(self, command: AssignmentCommand) -> None:
        await self._ensure_both_exist(command)
        await self._assignees.assign(command.project_id, command.member_id)
        await self._audit_logs.add(
            AuditLog.project_assign(
                actor_id=command.actor_id,
                project_id=command.project_id,
                member_id=command.member_id,
            )
        )


class UnassignMemberUseCase(_AssignmentUseCase):
    """Retire une personne des intervenants d'une mission."""

    async def execute(self, command: AssignmentCommand) -> None:
        await self._ensure_both_exist(command)
        await self._assignees.unassign(command.project_id, command.member_id)
        await self._audit_logs.add(
            AuditLog.project_unassign(
                actor_id=command.actor_id,
                project_id=command.project_id,
                member_id=command.member_id,
            )
        )
