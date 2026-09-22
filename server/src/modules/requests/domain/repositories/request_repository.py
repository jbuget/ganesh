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
    async def list_readable_by(self, viewer_id: int) -> list[Request]:
        """What the team reads, through the eyes of one of them.

        Everything that has been handed over, plus that person's own drafts: a
        need being written is its author's alone, and theirs is not somebody
        else's to be hidden from them.
        """
        ...

    @abstractmethod
    async def add(self, request: Request) -> Request: ...

    @abstractmethod
    async def update(self, request: Request) -> Request: ...

    @abstractmethod
    async def delete(self, request_id: int) -> None: ...
