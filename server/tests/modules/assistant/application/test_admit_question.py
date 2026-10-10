"""Admitting a question: everything that refuses one, before a model is paid."""

from uuid import uuid4

import pytest

from src.modules.assistant.application.dtos.assistant_dtos import AskCommand
from src.modules.assistant.application.use_cases.admit_question import (
    AdmitQuestionUseCase,
)
from src.modules.assistant.domain.entities.conversation import (
    MAX_EXCHANGES,
    Conversation,
    ConversationOverError,
)
from src.modules.projects.domain.entities.project import Project, ProjectKind
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from tests.helpers.assistant import ANSWER
from tests.helpers.in_memory_repositories import (
    InMemoryExchangeRepository,
    InMemoryProjectRepository,
)
from tests.helpers.instants import paris

WAATCHER = Project(id=7, label="WAATcher", kind=ProjectKind.PROJECT)


def admit(exchanges: InMemoryExchangeRepository) -> AdmitQuestionUseCase:
    return AdmitQuestionUseCase(
        exchanges=exchanges, projects=InMemoryProjectRepository([WAATCHER])
    )


async def a_conversation_kept_in(
    exchanges: InMemoryExchangeRepository, held: int, asker_id: int = 1
) -> Conversation:
    conversation = Conversation.opened(asker_id)
    for _ in range(held):
        await exchanges.add(
            conversation.record("Question ?", ANSWER, None, paris(2026, 10, 10, 9))
        )
    return conversation


async def test_a_first_question_opens_a_conversation_of_its_own() -> None:
    admitted = await admit(InMemoryExchangeRepository()).execute(
        AskCommand(asker_id=1, question="  Où en est WAATcher ?  ", project_id=7)
    )

    assert admitted.conversation.asker_id == 1
    assert admitted.conversation.exchanges == []
    assert admitted.question == "Où en est WAATcher ?"
    assert admitted.project_id == 7


async def test_a_follow_up_finds_the_conversation_and_what_was_said_in_it() -> None:
    exchanges = InMemoryExchangeRepository()
    held = await a_conversation_kept_in(exchanges, 2)

    admitted = await admit(exchanges).execute(
        AskCommand(asker_id=1, question="Et après ?", conversation_id=held.id)
    )

    assert admitted.conversation.id == held.id
    assert len(admitted.conversation.exchanges) == 2


async def test_a_sixth_question_is_refused() -> None:
    exchanges = InMemoryExchangeRepository()
    held = await a_conversation_kept_in(exchanges, MAX_EXCHANGES)

    with pytest.raises(ConversationOverError):
        await admit(exchanges).execute(
            AskCommand(asker_id=1, question="Encore ?", conversation_id=held.id)
        )


async def test_somebody_else_s_conversation_is_not_found() -> None:
    exchanges = InMemoryExchangeRepository()
    held = await a_conversation_kept_in(exchanges, 1, asker_id=1)

    with pytest.raises(EntityNotFoundError):
        await admit(exchanges).execute(
            AskCommand(asker_id=2, question="Et ?", conversation_id=held.id)
        )


async def test_a_conversation_nobody_opened_is_not_found() -> None:
    with pytest.raises(EntityNotFoundError):
        await admit(InMemoryExchangeRepository()).execute(
            AskCommand(asker_id=1, question="Et ?", conversation_id=uuid4())
        )


async def test_a_project_that_does_not_exist_is_dropped_rather_than_refused() -> None:
    admitted = await admit(InMemoryExchangeRepository()).execute(
        AskCommand(asker_id=1, question="Où en est-il ?", project_id=999)
    )

    assert admitted.project_id is None
