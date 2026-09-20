"""Provisions a user from their Entra identity."""

from datetime import datetime

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.domain.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.users.application.dtos.user_dto import EntraIdentity
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.utils import clock


class ProvisionUserUseCase:
    """Finds or creates the user matching an Entra identity.

    Matching goes by the Entra id first, then by email: that second case is
    what lets the seed pre-assign roles before the very first login.

    It is also the only place the API sees an identity go by: this is
    therefore where the last login is stamped, subject to the freshness window
    the domain holds.
    """

    def __init__(self, users: UserRepository, audit_logs: AuditLogRepository) -> None:
        self._users = users
        self._audit_logs = audit_logs

    async def execute(
        self, identity: EntraIdentity, now: datetime | None = None
    ) -> User:
        now = now or clock.now()

        existing = await self._users.get_by_entra_oid(identity.oid)
        if existing is not None:
            if existing.record_login(now):
                return await self._users.update(existing)
            return existing

        seeded = await self._users.get_by_email(identity.email)
        if seeded is not None:
            seeded.entra_oid = identity.oid
            seeded.display_name = identity.display_name or seeded.display_name
            seeded.record_login(now)
            return await self._users.update(seeded)

        created = await self._users.add(
            User(
                id=None,
                entra_oid=identity.oid,
                email=identity.email,
                display_name=identity.display_name,
                role=Role.TEAMMATE,
                last_login_at=now,
            )
        )
        assert created.id is not None
        # An account coming into being is traced like everything that happens
        # to it afterwards. Only the creation: a line per sign-in would bury
        # the log under what nobody decided.
        await self._audit_logs.add(
            AuditLog(
                action=AuditAction.USER_CREATE,
                actor_id=created.id,
                target_user_id=created.id,
                at=now,
                new_value=created.email,
            )
        )
        return created
