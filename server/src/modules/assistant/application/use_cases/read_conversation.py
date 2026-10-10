"""One conversation, whole, whoever had it."""

from uuid import UUID

from src.modules.assistant.domain.entities.conversation import Conversation
from src.modules.assistant.domain.repositories.exchange_archive import (
    ExchangeArchive,
)
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


class ReadConversationUseCase:
    """Every exchange of a conversation, with what each tool read back."""

    def __init__(self, archive: ExchangeArchive) -> None:
        self._archive = archive

    async def execute(self, conversation_id: UUID) -> Conversation:
        conversation = await self._archive.read_conversation(conversation_id)
        if conversation is None:
            raise EntityNotFoundError("This conversation does not exist.")
        return conversation
