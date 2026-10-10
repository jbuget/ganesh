"""Arranging one's own sidebar: which screens one would rather not see."""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.users.application.dtos.user_dto import ChooseOwnHiddenScreensCommand
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)


class ChooseOwnHiddenScreensUseCase:
    """Records which screens a teammate keeps off their own bar.

    The choice is kept on the account rather than in the browser so that it
    follows the person from one machine to the next. It is traced like the
    cadence is: a setting somebody changed is a gesture, even a quiet one.
    """

    def __init__(self, users: UserRepository, audit_logs: AuditLogRepository) -> None:
        self._users = users
        self._audit_logs = audit_logs

    async def execute(self, command: ChooseOwnHiddenScreensCommand) -> User:
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("The user cannot be found.")
        if not actor.can_arrange_own_navigation():
            raise ForbiddenActionError("This account cannot arrange its sidebar.")

        actor.choose_hidden_screens(command.screens)
        await self._users.update(actor)

        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.USER_NAVIGATION_CHOOSE,
                actor_id=command.actor_id,
                target_user_id=command.actor_id,
                payload={"hidden_screens": list(actor.hidden_screens)},
            )
        )
        return actor
