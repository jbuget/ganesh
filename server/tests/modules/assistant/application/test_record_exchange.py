"""Keeping an exchange once it has been answered."""

from src.modules.assistant.application.dtos.assistant_dtos import (
    AdmittedQuestion,
    RecordCommand,
)
from src.modules.assistant.application.use_cases.record_exchange import (
    RecordExchangeUseCase,
)
from src.modules.assistant.domain.entities.conversation import (
    MAX_EXCHANGES,
    Conversation,
)
from tests.helpers.assistant import ANSWER
from tests.helpers.in_memory_repositories import InMemoryExchangeRepository


async def test_the_exchange_is_kept_whole_at_the_next_rank() -> None:
    exchanges = InMemoryExchangeRepository()
    admitted = AdmittedQuestion(
        conversation=Conversation.opened(1),
        question="Où en est WAATcher ?",
        project_id=7,
    )

    kept = await RecordExchangeUseCase(exchanges).execute(
        RecordCommand(admitted=admitted, answer=ANSWER)
    )

    assert kept.exchange.id is not None
    assert kept.exchange.rank == 1
    assert kept.exchange.question == "Où en est WAATcher ?"
    assert kept.exchange.answer == ANSWER
    assert kept.exchange.project_id == 7
    assert kept.remaining == MAX_EXCHANGES - 1
    assert list(exchanges.exchanges.values()) == [kept.exchange]
