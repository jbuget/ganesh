"""Makes an account exist before its owner has ever signed in."""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.users.application.dtos.user_dto import DeclareUserCommand
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import (
    ConflictError,
    EntityNotFoundError,
    ForbiddenActionError,
)


class DeclareUserUseCase:
    """Declares a teammate. Managers and admins.

    An account otherwise comes into being on its owner's first sign-in, at the
    bottom of the ladder, and whoever is arriving on Monday can be put on no
    mission before they have signed in. Declaring is that wait removed: the
    sheet is filled in the day one knows somebody is coming, and their first
    sign-in claims the account by its address rather than opening a second
    one.
    """

    def __init__(self, users: UserRepository, audit_logs: AuditLogRepository) -> None:
        self._users = users
        self._audit_logs = audit_logs

    async def execute(self, command: DeclareUserCommand) -> User:
        actor = await self._users.get_by_id(command.actor_id)
        if actor is None:
            raise EntityNotFoundError("The user cannot be found.")
        if not actor.can_declare_user():
            raise ForbiddenActionError("Only a manager can declare a teammate.")
        if not actor.can_grant(command.role):
            raise ForbiddenActionError("Nobody confers a rank above their own.")

        # The address is what the first sign-in matches on: two accounts at one
        # address would mean one of them could never be claimed.
        if await self._users.get_by_email(command.email) is not None:
            raise ConflictError("An account already exists at this address.")

        created = await self._users.add(
            User.declared(
                email=command.email,
                first_name=command.first_name,
                last_name=command.last_name,
                role=command.role,
                department=command.department,
                github_username=command.github_username,
                org_level=command.org_level,
            )
        )
        assert created.id is not None
        # The actor is whoever declared the account, where provisioning names
        # the account itself: an account born of a decision says whose.
        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.USER_CREATE,
                actor_id=command.actor_id,
                target_user_id=created.id,
                new_value=created.email,
            )
        )
        return created
