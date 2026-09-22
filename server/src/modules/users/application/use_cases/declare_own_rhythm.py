"""Writing down how much of a week one works, from when."""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.calendar.domain.entities.week_pattern import WEEKDAYS
from src.modules.users.application.dtos.user_dto import DeclareOwnRhythmCommand
from src.modules.users.domain.entities.rhythm import Rhythm
from src.modules.users.domain.repositories.rhythm_repository import RhythmRepository
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)


class DeclareOwnRhythmUseCase:
    """Records the rhythm a teammate declares for themselves."""

    def __init__(
        self,
        users: UserRepository,
        rhythms: RhythmRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._users = users
        self._rhythms = rhythms
        self._audit_logs = audit_logs

    async def execute(self, command: DeclareOwnRhythmCommand) -> Rhythm:
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("The user cannot be found.")
        if not actor.can_declare_own_rhythm():
            raise ForbiddenActionError("This account cannot declare a rhythm.")

        declared = await self._rhythms.declare(
            Rhythm(
                id=None,
                user_id=command.actor_id,
                pattern=command.pattern,
                effective_from=command.effective_from,
            )
        )

        # The motif travels as a payload rather than as a before/after pair:
        # five days and a date change together, and a pair could only say one
        # of them. What is never asked for, and never written down, is why.
        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.USER_RHYTHM_DECLARE,
                actor_id=command.actor_id,
                target_user_id=command.actor_id,
                payload={
                    "effective_from": declared.effective_from.isoformat(),
                    **dict(zip(WEEKDAYS, declared.pattern.days, strict=True)),
                },
            )
        )
        return declared
