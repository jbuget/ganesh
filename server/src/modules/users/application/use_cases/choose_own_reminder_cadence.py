"""Saying how often one wants to be told, by mail, what is waiting."""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.users.application.dtos.user_dto import ChooseOwnReminderCadenceCommand
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)


class ChooseOwnReminderCadenceUseCase:
    """Records how often a teammate wants to be written to.

    Choosing is traced; the letters that follow are not. A cadence is a gesture
    somebody made, a letter is a channel — the same line the audit log already
    draws around a sign-in.
    """

    def __init__(self, users: UserRepository, audit_logs: AuditLogRepository) -> None:
        self._users = users
        self._audit_logs = audit_logs

    async def execute(self, command: ChooseOwnReminderCadenceCommand) -> User:
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("The user cannot be found.")
        if not actor.can_choose_own_reminder():
            raise ForbiddenActionError("This account cannot choose a cadence.")

        actor.choose_reminder_cadence(command.cadence)
        await self._users.update(actor)

        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.USER_REMINDER_CHOOSE,
                actor_id=command.actor_id,
                target_user_id=command.actor_id,
                payload={"cadence": command.cadence.value},
            )
        )
        return actor
