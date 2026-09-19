"""Changes a teammate's role."""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.users.application.dtos.user_dto import ChangeRoleCommand
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)


class ChangeUserRoleUseCase:
    """Promotes or demotes a teammate. Managers only."""

    def __init__(self, users: UserRepository, audit_logs: AuditLogRepository) -> None:
        self._users = users
        self._audit_logs = audit_logs

    async def execute(self, command: ChangeRoleCommand) -> User:
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("The user cannot be found.")
        if not actor.can_manage_teammates():
            raise ForbiddenActionError("Only a manager can change a teammate's role.")

        target = await self._users.get_by_id(command.target_user_id)
        if target is None:
            raise EntityNotFoundError("The teammate cannot be found.")

        previous = target.role
        target.role = command.role
        await self._users.update(target)

        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.USER_ROLE_CHANGE,
                actor_id=command.actor_id,
                target_user_id=command.target_user_id,
                old_value=previous.value,
                new_value=command.role.value,
            )
        )
        return target
