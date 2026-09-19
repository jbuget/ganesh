"""Port for the service accounts."""

from abc import ABC, abstractmethod

from src.modules.api_keys.domain.entities.api_key import ApiKey


class ApiKeyRepository(ABC):
    """Persistence contract for keys and the scopes they carry.

    Scopes travel with their key: they exist only through it and are read and
    written together, so they do not get a port of their own.
    """

    @abstractmethod
    async def add(self, key: ApiKey) -> ApiKey: ...

    @abstractmethod
    async def get_by_id(self, key_id: int) -> ApiKey | None: ...

    @abstractmethod
    async def get_by_public_id(self, public_id: str) -> ApiKey | None:
        """The key a token points at. One indexed row, never a scan."""
        ...

    @abstractmethod
    async def list_all(self) -> list[ApiKey]: ...

    @abstractmethod
    async def update(self, key: ApiKey) -> None: ...
