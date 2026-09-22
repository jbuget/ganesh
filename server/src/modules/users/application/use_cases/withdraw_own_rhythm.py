"""Taking one of one's own rhythms back out of the register."""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.users.application.dtos.user_dto import WithdrawOwnRhythmCommand
from src.modules.users.domain.repositories.rhythm_repository import RhythmRepository
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)


class WithdrawOwnRhythmUseCase:
    """Removes one rhythm a teammate declared for themselves.

    A history one may only add to is a history one cannot correct: a rhythm
    entered on the wrong date would hold its place for good, and the screen
    would go on announcing a change nobody meant to make.
    """

    def __init__(
        self,
        users: UserRepository,
        rhythms: RhythmRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._users = users
        self._rhythms = rhythms
        self._audit_logs = audit_logs

    async def execute(self, command: WithdrawOwnRhythmCommand) -> None:
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("The user cannot be found.")
        if not actor.can_declare_own_rhythm():
            raise ForbiddenActionError("This account cannot change a rhythm.")

        withdrawn = await self._rhythms.withdraw(
            command.actor_id, command.effective_from
        )
        if not withdrawn:
            # Said out loud rather than answered as a success: a removal that
            # did not happen must not read like one that did, or the screen
            # would stop showing a row the register still holds.
            raise EntityNotFoundError("No rhythm opens on that day.")

        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.USER_RHYTHM_WITHDRAW,
                actor_id=command.actor_id,
                target_user_id=command.actor_id,
                payload={"effective_from": command.effective_from.isoformat()},
            )
        )
