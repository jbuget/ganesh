"""Keeping an exchange once it has been answered."""

from src.modules.assistant.application.dtos.assistant_dtos import (
    AskResult,
    RecordCommand,
)
from src.modules.assistant.domain.repositories.exchange_repository import (
    ExchangeRepository,
)
from src.shared.utils import clock


class RecordExchangeUseCase:
    """Keeps the question, the answer and the tools' readings, whole.

    So that the assistant can be studied and improved. An answer that never
    came is never handed here: there is nothing to study in it that the logs do
    not already say.
    """

    def __init__(self, exchanges: ExchangeRepository) -> None:
        self._exchanges = exchanges

    async def execute(self, command: RecordCommand) -> AskResult:
        admitted = command.admitted
        conversation = admitted.conversation
        exchange = conversation.record(
            admitted.question,
            command.answer,
            project_id=admitted.project_id,
            asked_at=clock.now(),
        )
        return AskResult(
            exchange=await self._exchanges.add(exchange),
            remaining=conversation.remaining,
        )
