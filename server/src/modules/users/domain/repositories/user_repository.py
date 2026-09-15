"""Port d'acces aux utilisateurs."""

from abc import ABC, abstractmethod

from src.modules.users.domain.entities.user import User


class UserRepository(ABC):
    """Contrat de persistance des utilisateurs."""

    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None: ...

    @abstractmethod
    async def get_by_entra_oid(self, entra_oid: str) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def list_all(self, include_inactive: bool = False) -> list[User]: ...

    @abstractmethod
    async def add(self, user: User) -> User: ...

    @abstractmethod
    async def update(self, user: User) -> User: ...
