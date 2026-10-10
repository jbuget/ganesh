"""A thumb up or down under an answer: what makes the kept exchanges studiable."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.modules.assistant.application.dtos.assistant_dtos import JudgeCommand
from src.modules.assistant.application.use_cases.judge_answer import JudgeAnswerUseCase
from src.modules.assistant.domain.entities.exchange import Answer, Exchange, Verdict
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from tests.helpers.in_memory_repositories import InMemoryExchangeRepository


async def an_exchange_kept_in(exchanges: InMemoryExchangeRepository) -> Exchange:
    return await exchanges.add(
        Exchange(
            conversation_id=uuid4(),
            rank=1,
            asker_id=1,
            question="Où en est WAATcher ?",
            answer=Answer("Réponse.", (), "gemini-test", 10, 5, 300),
            project_id=None,
            asked_at=datetime(2026, 10, 10, tzinfo=UTC),
        )
    )


async def test_whoever_asked_judges_the_answer() -> None:
    exchanges = InMemoryExchangeRepository()
    kept = await an_exchange_kept_in(exchanges)
    assert kept.id is not None

    judged = await JudgeAnswerUseCase(exchanges).execute(
        JudgeCommand(exchange_id=kept.id, judge_id=1, verdict=Verdict.HELPFUL)
    )

    assert judged.verdict is Verdict.HELPFUL
    assert exchanges.exchanges[kept.id].verdict is Verdict.HELPFUL


async def test_somebody_else_s_answer_is_not_found_for_them() -> None:
    """Whether it exists is none of their business, as for a conversation."""
    exchanges = InMemoryExchangeRepository()
    kept = await an_exchange_kept_in(exchanges)
    assert kept.id is not None

    with pytest.raises(EntityNotFoundError):
        await JudgeAnswerUseCase(exchanges).execute(
            JudgeCommand(exchange_id=kept.id, judge_id=2, verdict=Verdict.HELPFUL)
        )
    assert exchanges.exchanges[kept.id].verdict is None


async def test_an_answer_nobody_gave_is_not_found() -> None:
    with pytest.raises(EntityNotFoundError):
        await JudgeAnswerUseCase(InMemoryExchangeRepository()).execute(
            JudgeCommand(exchange_id=99, judge_id=1, verdict=Verdict.HELPFUL)
        )
