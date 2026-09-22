"""Port for the needs the company expresses."""

from abc import ABC, abstractmethod

from src.modules.requests.domain.entities.request import Request


class RequestRepository(ABC):
    """Persistence contract for requests."""

    @abstractmethod
    async def get_by_id(self, request_id: int) -> Request | None: ...

    @abstractmethod
    async def list_for_requester(self, requester_id: int) -> list[Request]:
        """Everything one person filed, drafts included: they are all theirs."""
        ...

    @abstractmethod
    async def list_all(self, include_drafts: bool = False) -> list[Request]:
        """What the team reads.

        Drafts are left out by default: a need being written is its author's
        alone until they hand it over.
        """
        ...

    @abstractmethod
    async def add(self, request: Request) -> Request: ...

    @abstractmethod
    async def update(self, request: Request) -> Request: ...

    @abstractmethod
    async def delete(self, request_id: int) -> None: ...
