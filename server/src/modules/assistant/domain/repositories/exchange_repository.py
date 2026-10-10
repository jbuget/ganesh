"""Port for the exchanges kept with the assistant."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.modules.assistant.domain.entities.conversation import Conversation
from src.modules.assistant.domain.entities.exchange import Exchange


class ExchangeRepository(ABC):
    @abstractmethod
    async def get_conversation(
        self, conversation_id: UUID, asker_id: int
    ) -> Conversation | None:
        """The conversation, if it exists and was opened by this person.

        Somebody else's comes back as nothing at all: whether it exists is
        none of their business.
        """
        ...

    @abstractmethod
    async def add(self, exchange: Exchange) -> Exchange:
        """Keeps an exchange and hands it back with its identifier.

        Raises `ConflictError` when the conversation already holds an exchange
        at that rank: two questions asked at once from two tabs.
        """
        ...

    @abstractmethod
    async def get(self, exchange_id: int, asker_id: int) -> Exchange | None:
        """The exchange, if this person had it. Anybody else's reads as none."""
        ...

    @abstractmethod
    async def save_verdict(self, exchange: Exchange) -> None: ...
