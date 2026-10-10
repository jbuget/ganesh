"""Asking the assistant: one question admitted, answered, and kept.

Played through the real use cases on in-memory repositories, with a scripted
model: what is under test is the order — nothing reaches the model that the
conversation refuses, and what the model could not answer is kept apart from
the exchanges, with why.
"""

from uuid import uuid4

import pytest

from src.assistant.answerer import Answerer
from src.assistant.asking import ask
from src.modules.assistant.application.dtos.assistant_dtos import AskCommand, AskResult
from src.modules.assistant.application.use_cases.admit_question import (
    AdmitQuestionUseCase,
)
from src.modules.assistant.application.use_cases.record_exchange import (
    RecordExchangeUseCase,
)
from src.modules.assistant.application.use_cases.record_unanswered import (
    RecordUnansweredUseCase,
)
from src.modules.assistant.domain.entities.conversation import (
    MAX_EXCHANGES,
    ConversationOverError,
)
from src.modules.assistant.domain.entities.unanswered import (
    UnansweredQuestion,
    WhyUnanswered,
)
from src.modules.projects.domain.entities.project import Project, ProjectKind
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ServiceUnavailableError,
    ValidationError,
)
from tests.helpers.assistant import ANSWER, UNANSWERED, ScriptedAnswerer
from tests.helpers.in_memory_repositories import (
    InMemoryExchangeRepository,
    InMemoryProjectRepository,
    InMemoryUnansweredQuestionRepository,
)

WAATCHER = Project(id=7, label="WAATcher", kind=ProjectKind.PROJECT)


class Asking:
    """The way in, wired on in-memory repositories."""

    def __init__(self, exchanges: InMemoryExchangeRepository, answerer: Answerer):
        self._admit = AdmitQuestionUseCase(
            exchanges=exchanges, projects=InMemoryProjectRepository([WAATCHER])
        )
        self._record = RecordExchangeUseCase(exchanges)
        self.unanswered = InMemoryUnansweredQuestionRepository()
        self._record_unanswered = RecordUnansweredUseCase(self.unanswered)
        self._answerer = answerer

    async def attempt(self, command: AskCommand) -> AskResult | UnansweredQuestion:
        return await ask(
            command,
            admit=self._admit,
            answerer=self._answerer,
            record=self._record,
            record_unanswered=self._record_unanswered,
        )

    async def execute(self, command: AskCommand) -> AskResult:
        asked = await self.attempt(command)
        assert isinstance(asked, AskResult)
        return asked


def ask_with(exchanges: InMemoryExchangeRepository, answerer: Answerer) -> Asking:
    return Asking(exchanges, answerer)


def asking(question: str = "Où en est WAATcher ?", **fields: object) -> AskCommand:
    return AskCommand(
        asker_id=fields.get("asker_id", 1),  # type: ignore[arg-type]
        question=question,
        conversation_id=fields.get("conversation_id"),  # type: ignore[arg-type]
        project_id=fields.get("project_id"),  # type: ignore[arg-type]
    )


@pytest.fixture
def exchanges() -> InMemoryExchangeRepository:
    return InMemoryExchangeRepository()


async def test_a_first_question_opens_a_conversation_and_keeps_the_exchange(
    exchanges: InMemoryExchangeRepository,
) -> None:
    use_case = ask_with(exchanges, ScriptedAnswerer())

    asked = await use_case.execute(asking(project_id=7))

    assert asked.exchange.id is not None
    assert asked.exchange.rank == 1
    assert asked.exchange.question == "Où en est WAATcher ?"
    assert asked.exchange.answer == ANSWER
    assert asked.exchange.project_id == 7
    assert asked.remaining == MAX_EXCHANGES - 1
    assert list(exchanges.exchanges.values()) == [asked.exchange]


async def test_a_follow_up_is_answered_with_the_conversation_so_far(
    exchanges: InMemoryExchangeRepository,
) -> None:
    answerer = ScriptedAnswerer()
    use_case = ask_with(exchanges, answerer)
    first = await use_case.execute(asking())

    second = await use_case.execute(
        asking(
            "Et depuis quinze jours ?", conversation_id=first.exchange.conversation_id
        )
    )

    assert second.exchange.rank == 2
    assert second.exchange.conversation_id == first.exchange.conversation_id
    assert answerer.asked[-1] == (1, "Et depuis quinze jours ?", None)


async def test_the_question_is_asked_without_its_surrounding_blanks(
    exchanges: InMemoryExchangeRepository,
) -> None:
    answerer = ScriptedAnswerer()

    await ask_with(exchanges, answerer).execute(asking("  Où en est WAATcher ?  "))

    assert answerer.asked == [(0, "Où en est WAATcher ?", None)]


async def test_a_sixth_question_is_refused_before_the_model_is_asked(
    exchanges: InMemoryExchangeRepository,
) -> None:
    answerer = ScriptedAnswerer()
    use_case = ask_with(exchanges, answerer)
    opened = await use_case.execute(asking())
    for _ in range(MAX_EXCHANGES - 1):
        await use_case.execute(asking(conversation_id=opened.exchange.conversation_id))

    with pytest.raises(ConversationOverError):
        await use_case.execute(asking(conversation_id=opened.exchange.conversation_id))
    assert len(answerer.asked) == MAX_EXCHANGES


async def test_an_empty_question_never_reaches_the_model(
    exchanges: InMemoryExchangeRepository,
) -> None:
    answerer = ScriptedAnswerer()

    with pytest.raises(ValidationError):
        await ask_with(exchanges, answerer).execute(asking("  "))
    assert answerer.asked == []


async def test_nobody_carries_on_somebody_else_s_conversation(
    exchanges: InMemoryExchangeRepository,
) -> None:
    use_case = ask_with(exchanges, ScriptedAnswerer())
    theirs = await use_case.execute(asking(asker_id=1))

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(
            asking(asker_id=2, conversation_id=theirs.exchange.conversation_id)
        )


async def test_a_conversation_nobody_opened_is_not_found(
    exchanges: InMemoryExchangeRepository,
) -> None:
    use_case = ask_with(exchanges, ScriptedAnswerer())

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(asking(conversation_id=uuid4()))


async def test_without_a_model_the_assistant_says_it_is_unavailable(
    exchanges: InMemoryExchangeRepository,
) -> None:
    use_case = ask_with(exchanges, ScriptedAnswerer(available=False))

    with pytest.raises(ServiceUnavailableError):
        await use_case.execute(asking())


async def test_a_question_left_unanswered_is_kept_apart_with_why(
    exchanges: InMemoryExchangeRepository,
) -> None:
    """Kept to study it, and taking no place among the exchanges."""
    use_case = ask_with(exchanges, ScriptedAnswerer(answer=UNANSWERED))

    missed = await use_case.attempt(asking("Qui fait quoi ?", project_id=7))

    assert isinstance(missed, UnansweredQuestion)
    assert exchanges.exchanges == {}
    [kept] = use_case.unanswered.questions.values()
    assert (kept.question, kept.project_id) == ("Qui fait quoi ?", 7)
    assert kept.unanswered.reason is WhyUnanswered.KEPT_ASKING
    assert kept.unanswered.consultations == UNANSWERED.consultations


async def test_a_project_that_does_not_exist_is_not_taken_for_the_one_in_view(
    exchanges: InMemoryExchangeRepository,
) -> None:
    """An address kept from a deleted project names nothing: the question stands."""
    answerer = ScriptedAnswerer()

    asked = await ask_with(exchanges, answerer).execute(asking(project_id=999))

    assert answerer.asked == [(0, "Où en est WAATcher ?", None)]
    assert asked.exchange.project_id is None
