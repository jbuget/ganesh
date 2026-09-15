"""Provisionne un utilisateur a partir de son identite Entra."""

from src.modules.users.application.dtos.user_dto import EntraIdentity
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.domain.repositories.user_repository import UserRepository


class ProvisionUserUseCase:
    """Retrouve ou cree l'utilisateur correspondant a une identite Entra.

    Le rapprochement se fait d'abord sur l'identifiant Entra, puis sur l'email :
    c'est ce second cas qui permet au seed de pre-attribuer les roles avant la
    toute premiere connexion.
    """

    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def execute(self, identity: EntraIdentity) -> User:
        existing = await self._users.get_by_entra_oid(identity.oid)
        if existing is not None:
            return existing

        seeded = await self._users.get_by_email(identity.email)
        if seeded is not None:
            seeded.entra_oid = identity.oid
            seeded.display_name = identity.display_name or seeded.display_name
            return await self._users.update(seeded)

        return await self._users.add(
            User(
                id=None,
                entra_oid=identity.oid,
                email=identity.email,
                display_name=identity.display_name,
                role=Role.TEAMMATE,
            )
        )
