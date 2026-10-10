"""What a period of exchanges says about the assistant."""

from src.modules.assistant.application.dtos.assistant_dtos import AssistantIndicators
from src.modules.assistant.domain.repositories.exchange_archive import (
    ExchangeArchive,
    ExchangeFilter,
)
from src.modules.assistant.domain.services.indicators import indicators_of


class ReadIndicatorsUseCase:
    """Counts the exchanges the filter keeps, the questions left unanswered
    beside them, and says how far back they go."""

    def __init__(self, archive: ExchangeArchive) -> None:
        self._archive = archive

    async def execute(self, kept: ExchangeFilter) -> AssistantIndicators:
        unanswered = await self._archive.list_unanswered(kept, limit=1, offset=0)
        return AssistantIndicators(
            indicators=indicators_of(await self._archive.list_exchanges(kept)),
            kept_since=await self._archive.kept_since(),
            unanswered=unanswered.total,
        )
