"""Gives away who a teammate is, and where they work."""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.users.application.dtos.user_dto import UpdateUserIdentityCommand
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)


class UpdateUserIdentityUseCase:
    """Rewrites a teammate's civil name and department. Managers only."""

    def __init__(self, users: UserRepository, audit_logs: AuditLogRepository) -> None:
        self._users = users
        self._audit_logs = audit_logs

    async def execute(self, command: UpdateUserIdentityCommand) -> User:
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("The user cannot be found.")
        if not actor.can_manage_teammates():
            raise ForbiddenActionError(
                "Only a manager can change a teammate's identity."
            )

        target = await self._users.get_by_id(command.target_user_id)
        if target is None:
            raise EntityNotFoundError("The teammate cannot be found.")

        target.set_identity(
            first_name=command.first_name,
            last_name=command.last_name,
            department=command.department,
            github_username=command.github_username,
        )
        await self._users.update(target)

        # Four fields at once: the trace carries them as a payload rather than
        # as one before/after pair, which could only say one of them.
        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.USER_IDENTITY_UPDATE,
                actor_id=command.actor_id,
                target_user_id=command.target_user_id,
                payload={
                    "first_name": target.first_name,
                    "last_name": target.last_name,
                    "department": (
                        target.department.value if target.department else None
                    ),
                    "github_username": target.github_username,
                },
            )
        )
        return target
