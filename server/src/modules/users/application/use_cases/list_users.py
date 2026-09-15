"""Liste les collaborateurs."""

from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository


class ListUsersUseCase:
    """Retourne les collaborateurs, actifs par defaut."""

    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def execute(self, include_inactive: bool = False) -> list[User]:
        return await self._users.list_all(include_inactive=include_inactive)
