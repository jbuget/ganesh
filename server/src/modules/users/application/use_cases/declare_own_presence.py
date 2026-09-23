"""Saying which days one works, and from where."""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.users.application.dtos.user_dto import DeclareOwnPresenceCommand
from src.modules.users.domain.entities.presence import WEEKDAYS
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)


class DeclareOwnPresenceUseCase:
    """Records the ordinary week a teammate declares for themselves."""

    def __init__(self, users: UserRepository, audit_logs: AuditLogRepository) -> None:
        self._users = users
        self._audit_logs = audit_logs

    async def execute(self, command: DeclareOwnPresenceCommand) -> User:
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("The user cannot be found.")
        if not actor.can_declare_own_presence():
            raise ForbiddenActionError("This account cannot declare a week.")

        actor.presence = command.week
        await self._users.update(actor)

        # The five days travel as a payload rather than as a before/after pair,
        # which could only ever say one of them.
        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.USER_PRESENCE_DECLARE,
                actor_id=command.actor_id,
                target_user_id=command.actor_id,
                payload={day: getattr(command.week, day).value for day in WEEKDAYS},
            )
        )
        return actor
