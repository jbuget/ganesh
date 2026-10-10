"""A thumb up or down under an answer."""

from src.modules.assistant.application.dtos.assistant_dtos import JudgeCommand
from src.modules.assistant.domain.entities.exchange import Exchange
from src.modules.assistant.domain.repositories.exchange_repository import (
    ExchangeRepository,
)
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


class JudgeAnswerUseCase:
    """Records whether an answer helped: what turns kept exchanges into a sample."""

    def __init__(self, exchanges: ExchangeRepository) -> None:
        self._exchanges = exchanges

    async def execute(self, command: JudgeCommand) -> Exchange:
        exchange = await self._exchanges.get(command.exchange_id, command.judge_id)
        if exchange is None:
            raise EntityNotFoundError("This answer does not exist.")

        exchange.judge(by=command.judge_id, verdict=command.verdict)
        await self._exchanges.save_verdict(exchange)
        return exchange
