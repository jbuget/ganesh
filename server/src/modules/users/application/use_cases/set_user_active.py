"""Cuts off or restores a teammate's access."""

from datetime import datetime

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.notifications.domain.services.fan_out import notify
from src.modules.users.application.dtos.user_dto import SetUserActiveCommand
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)


class SetUserActiveUseCase:
    """Deactivates or reactivates a teammate. Managers only.

    Deactivating deletes nothing: past entries stay in the database and go on
    feeding the per-project totals. Only access is cut off.
    """

    def __init__(
        self,
        users: UserRepository,
        audit_logs: AuditLogRepository,
        notifications: NotificationDelivery,
    ) -> None:
        self._users = users
        self._audit_logs = audit_logs
        self._notifications = notifications

    async def execute(self, command: SetUserActiveCommand) -> User:
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("The user cannot be found.")

        target = await self._users.get_by_id(command.target_user_id)
        if target is None:
            raise EntityNotFoundError("The teammate cannot be found.")

        if not self._is_allowed(actor, target, command.is_active):
            raise ForbiddenActionError(
                "Only a manager can cut off a teammate's access, "
                "and nobody can cut off their own."
            )

        previous = target.is_active
        if previous == command.is_active:
            # A click with no effect has no business leaving a trace.
            return target

        target.is_active = command.is_active
        await self._users.update(target)

        await self._audit_logs.add(
            AuditLog(
                action=(
                    AuditAction.USER_ACTIVATE
                    if command.is_active
                    else AuditAction.USER_DEACTIVATE
                ),
                actor_id=command.actor_id,
                target_user_id=command.target_user_id,
                old_value=str(previous),
                new_value=str(command.is_active),
            )
        )
        # A deactivated account cannot sign in, so the line waits: it is read
        # on the way back, which is exactly when one wants to know what
        # happened while one was away.
        await self._notifications.deliver(
            notify(
                (
                    NotificationKind.USER_ACTIVATED
                    if command.is_active
                    else NotificationKind.USER_DEACTIVATED
                ),
                actor_id=command.actor_id,
                recipients=[command.target_user_id],
                at=datetime.now(),
            )
        )
        return target

    @staticmethod
    def _is_allowed(actor: User, target: User, is_active: bool) -> bool:
        """Restoring access locks nobody out: only cutting off is restrained."""
        if is_active:
            return actor.can_manage_teammates()
        return actor.can_deactivate(target)
