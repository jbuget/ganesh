"""From the assistant's DTOs to what the API hands over."""

from src.modules.assistant.application.dtos.assistant_dtos import (
    AskResult,
    AssistantStatus,
)
from src.modules.assistant.presentation.api.schemas.assistant_schemas import (
    AssistantStatusResponse,
    ExchangeResponse,
)


def to_status_response(status: AssistantStatus) -> AssistantStatusResponse:
    return AssistantStatusResponse(
        is_available=status.is_available, max_exchanges=status.max_exchanges
    )


def to_exchange_response(asked: AskResult) -> ExchangeResponse:
    exchange = asked.exchange
    assert exchange.id is not None
    return ExchangeResponse(
        id=exchange.id,
        conversation_id=exchange.conversation_id,
        rank=exchange.rank,
        remaining=asked.remaining,
        question=exchange.question,
        answer=exchange.answer.text,
        consulted_project_ids=list(exchange.answer.consulted_project_ids),
        verdict=exchange.verdict,
    )
