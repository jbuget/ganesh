"""Every question the assistant could not answer, to study why."""

from src.modules.assistant.domain.repositories.exchange_archive import (
    ExchangeArchive,
    ExchangeFilter,
    UnansweredPage,
)


class ListUnansweredUseCase:
    """The questions left unanswered the filter keeps, latest first, paged."""

    def __init__(self, archive: ExchangeArchive) -> None:
        self._archive = archive

    async def execute(
        self, kept: ExchangeFilter, limit: int, offset: int
    ) -> UnansweredPage:
        return await self._archive.list_unanswered(kept, limit, offset)
