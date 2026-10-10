"""What the panel needs to know before anybody types a question."""

from src.modules.assistant.application.use_cases.read_assistant import (
    ReadAssistantUseCase,
)
from src.modules.assistant.domain.entities.conversation import MAX_EXCHANGES


async def test_a_configured_model_answers_for_as_long_as_a_conversation_runs() -> None:
    status = await ReadAssistantUseCase(is_configured=True).execute()

    assert status.is_available
    assert status.max_exchanges == MAX_EXCHANGES


async def test_without_a_model_the_assistant_says_it_does_not_answer() -> None:
    status = await ReadAssistantUseCase(is_configured=False).execute()

    assert not status.is_available
