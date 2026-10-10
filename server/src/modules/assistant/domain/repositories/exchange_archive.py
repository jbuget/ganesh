"""Port for reading every exchange kept, whoever asked it.

Apart from `ExchangeRepository` on purpose. That one answers the person in
the panel, and somebody else's conversation reads there as nothing at all;
this one answers an administrator studying the assistant, and reads them all.
Two ports keep the first rule from being one forgotten argument away.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from src.modules.assistant.domain.entities.conversation import Conversation
from src.modules.assistant.domain.entities.exchange import Exchange


class Judgement(StrEnum):
    """What whoever asked said of the answer, silence included."""

    HELPFUL = "helpful"
    UNHELPFUL = "unhelpful"
    UNJUDGED = "unjudged"


@dataclass(frozen=True)
class ExchangeFilter:
    """Which exchanges to read. Every criterion left out reads them all."""

    since: datetime | None = None
    until: datetime | None = None
    asker_id: int | None = None
    judgement: Judgement | None = None


@dataclass(frozen=True)
class ConversationPage:
    conversations: list[Conversation]
    #: Every conversation the filter holds, not only the page.
    total: int


class ExchangeArchive(ABC):
    @abstractmethod
    async def list_conversations(
        self, kept: ExchangeFilter, limit: int, offset: int
    ) -> ConversationPage:
        """The conversations holding an exchange the filter keeps, latest first.

        Each comes back whole: an exchange read without the ones before it
        cannot be understood.
        """
        ...

    @abstractmethod
    async def read_conversation(self, conversation_id: UUID) -> Conversation | None: ...

    @abstractmethod
    async def list_exchanges(self, kept: ExchangeFilter) -> list[Exchange]:
        """The exchanges the filter keeps, oldest first."""
        ...

    @abstractmethod
    async def read_exchange(self, exchange_id: int) -> Exchange | None: ...

    @abstractmethod
    async def kept_since(self) -> datetime | None:
        """When the oldest exchange still kept was asked, if any is."""
        ...

    @abstractmethod
    async def save_annotation(self, exchange: Exchange) -> None: ...
