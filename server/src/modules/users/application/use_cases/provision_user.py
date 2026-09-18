"""Provisions a user from their Entra identity."""

from datetime import datetime

from src.modules.users.application.dtos.user_dto import EntraIdentity
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.domain.repositories.user_repository import UserRepository


class ProvisionUserUseCase:
    """Finds or creates the user matching an Entra identity.

    Matching goes by the Entra id first, then by email: that second case is
    what lets the seed pre-assign roles before the very first login.

    It is also the only place the API sees an identity go by: this is
    therefore where the last login is stamped, subject to the freshness window
    the domain holds.
    """

    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def execute(
        self, identity: EntraIdentity, now: datetime | None = None
    ) -> User:
        now = now or datetime.now()

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

        return await self._users.add(
            User(
                id=None,
                entra_oid=identity.oid,
                email=identity.email,
                display_name=identity.display_name,
                role=Role.TEAMMATE,
                last_login_at=now,
            )
        )
