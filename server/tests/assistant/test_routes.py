"""The routes the assistant's panel calls.

Asking is `src.assistant`'s, reading the status and judging an answer are the
module's: the panel calls all three, and they are read here together, with the
model scripted and the repositories in memory.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient, Response

from src.assistant.dependencies import get_answerer
from src.core.config import get_settings
from src.main import app
from src.modules.assistant.application.use_cases.admit_question import (
    AdmitQuestionUseCase,
)
from src.modules.assistant.application.use_cases.judge_answer import JudgeAnswerUseCase
from src.modules.assistant.application.use_cases.read_assistant import (
    ReadAssistantUseCase,
)
from src.modules.assistant.application.use_cases.record_exchange import (
    RecordExchangeUseCase,
)
from src.modules.assistant.application.use_cases.record_unanswered import (
    RecordUnansweredUseCase,
)
from src.modules.assistant.domain.entities.conversation import MAX_EXCHANGES
from src.modules.assistant.domain.entities.exchange import Verdict
from src.modules.assistant.presentation.dependencies import (
    get_admit_question_use_case,
    get_judge_answer_use_case,
    get_read_assistant_use_case,
    get_record_exchange_use_case,
    get_record_unanswered_use_case,
)
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.projects.domain.entities.project import Project, ProjectKind
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.assistant import ANSWER, UNANSWERED, ScriptedAnswerer
from tests.helpers.in_memory_repositories import (
    InMemoryExchangeRepository,
    InMemoryProjectRepository,
    InMemoryUnansweredQuestionRepository,
)

SYLVAIN = User(
    id=4, entra_oid="oid-4", email="s@waat.fr", display_name="S. P", role=Role.MANAGER
)
LEA = User(
    id=1, entra_oid="oid-1", email="l@waat.fr", display_name="L. C", role=Role.TEAMMATE
)
WAATCHER = Project(id=7, label="WAATcher", kind=ProjectKind.PROJECT)
ASSISTANT = f"{get_settings().api_prefix}/assistant"


@dataclass
class Panel:
    client: AsyncClient
    exchanges: InMemoryExchangeRepository
    unanswered: InMemoryUnansweredQuestionRepository

    async def ask(
        self, question: str = "Où en est WAATcher ?", **fields: object
    ) -> Response:
        return await self.client.post(
            f"{ASSISTANT}/exchanges", json={"question": question, **fields}
        )

    async def judge(self, exchange_id: int, verdict: str) -> Response:
        return await self.client.put(
            f"{ASSISTANT}/exchanges/{exchange_id}/verdict", json={"verdict": verdict}
        )


def open_panel(
    person: User = SYLVAIN,
    answerer: ScriptedAnswerer | None = None,
    exchanges: InMemoryExchangeRepository | None = None,
) -> Panel:
    answerer = answerer or ScriptedAnswerer()
    exchanges = exchanges or InMemoryExchangeRepository()
    app.dependency_overrides[get_current_user] = lambda: person
    app.dependency_overrides[get_read_assistant_use_case] = (
        lambda: ReadAssistantUseCase(is_configured=answerer.is_available)
    )
    app.dependency_overrides[get_admit_question_use_case] = (
        lambda: AdmitQuestionUseCase(
            exchanges=exchanges, projects=InMemoryProjectRepository([WAATCHER])
        )
    )
    app.dependency_overrides[get_record_exchange_use_case] = (
        lambda: RecordExchangeUseCase(exchanges)
    )
    unanswered = InMemoryUnansweredQuestionRepository()
    app.dependency_overrides[get_record_unanswered_use_case] = (
        lambda: RecordUnansweredUseCase(unanswered)
    )
    app.dependency_overrides[get_answerer] = lambda: answerer
    app.dependency_overrides[get_judge_answer_use_case] = lambda: JudgeAnswerUseCase(
        exchanges
    )
    return Panel(
        client=AsyncClient(transport=ASGITransport(app=app), base_url="http://test"),
        exchanges=exchanges,
        unanswered=unanswered,
    )


@pytest.fixture(autouse=True)
def _forget_the_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


async def test_the_panel_learns_whether_it_may_ask_and_for_how_long() -> None:
    response = await open_panel().client.get(ASSISTANT)

    assert response.status_code == 200
    assert response.json() == {"is_available": True, "max_exchanges": MAX_EXCHANGES}


async def test_a_question_is_answered_and_kept() -> None:
    panel = open_panel()

    response = await panel.ask(project_id=7)

    assert response.status_code == 201
    body = response.json()
    assert body["rank"] == 1
    assert body["remaining"] == MAX_EXCHANGES - 1
    assert body["question"] == "Où en est WAATcher ?"
    assert body["answer"] == ANSWER.text
    assert body["consulted_project_ids"] == [7]
    assert body["verdict"] is None
    assert UUID(body["conversation_id"])
    assert len(panel.exchanges.exchanges) == 1


async def test_a_follow_up_carries_on_the_conversation() -> None:
    panel = open_panel()
    first = (await panel.ask()).json()

    second = await panel.ask("Et depuis ?", conversation_id=first["conversation_id"])

    assert second.status_code == 201
    assert second.json()["rank"] == 2


async def test_a_sixth_question_is_a_conflict() -> None:
    panel = open_panel()
    opened = (await panel.ask()).json()["conversation_id"]
    for _ in range(MAX_EXCHANGES - 1):
        await panel.ask(conversation_id=opened)

    response = await panel.ask(conversation_id=opened)

    assert response.status_code == 409


async def test_a_question_left_unanswered_is_kept_and_told_as_unavailable() -> None:
    """The panel says « indisponible » as before; the question is kept to study."""
    panel = open_panel(answerer=ScriptedAnswerer(answer=UNANSWERED))

    response = await panel.ask()

    assert response.status_code == 503
    assert panel.exchanges.exchanges == {}
    [kept] = panel.unanswered.questions.values()
    assert kept.question == "Où en est WAATcher ?"


async def test_without_a_model_the_question_is_turned_away_as_unavailable() -> None:
    response = await open_panel(answerer=ScriptedAnswerer(available=False)).ask()

    assert response.status_code == 503


async def test_an_empty_question_is_refused() -> None:
    response = await open_panel().ask("   ")

    assert response.status_code == 422


async def test_whoever_asked_judges_the_answer() -> None:
    panel = open_panel()
    asked = (await panel.ask()).json()

    response = await panel.judge(asked["id"], "unhelpful")

    assert response.status_code == 204
    assert panel.exchanges.exchanges[asked["id"]].verdict is Verdict.UNHELPFUL


async def test_somebody_else_s_answer_is_not_found_rather_than_forbidden() -> None:
    """Whether it exists is none of their business, as for a conversation."""
    exchanges = InMemoryExchangeRepository()
    asked = (await open_panel(SYLVAIN, exchanges=exchanges).ask()).json()

    response = await open_panel(LEA, exchanges=exchanges).judge(asked["id"], "helpful")

    assert response.status_code == 404


async def test_an_answer_nobody_gave_is_not_found() -> None:
    response = await open_panel().judge(999, "helpful")

    assert response.status_code == 404
