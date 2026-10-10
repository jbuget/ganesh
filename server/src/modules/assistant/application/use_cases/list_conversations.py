"""Every conversation kept, to study the assistant."""

from src.modules.assistant.domain.repositories.exchange_archive import (
    ConversationPage,
    ExchangeArchive,
    ExchangeFilter,
)


class ListConversationsUseCase:
    """The conversations holding an exchange the filter keeps, latest first, paged."""

    def __init__(self, archive: ExchangeArchive) -> None:
        self._archive = archive

    async def execute(
        self, kept: ExchangeFilter, limit: int, offset: int
    ) -> ConversationPage:
        return await self._archive.list_conversations(kept, limit, offset)
