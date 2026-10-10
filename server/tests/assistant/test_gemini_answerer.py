"""The loop between the model and the tools, played against a scripted Gemini.

No network here: what is under test is what the adapter does with what comes
back — a tool asked for, a tool read, an answer written, or a model that never
stops asking.
"""

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from google.genai import types

from src.assistant.gemini_answerer import (
    ENOUGH,
    MAX_CONSULTATIONS,
    MAX_ROUNDS,
    GeminiAnswerer,
)
from src.assistant.toolbox import Tool, Toolbox
from src.modules.assistant.domain.entities.conversation import Conversation
from src.modules.assistant.domain.entities.exchange import Answer, Consultation
from src.modules.assistant.domain.entities.unanswered import Unanswered, WhyUnanswered


async def project_brief(project_id: int) -> str:
    """Dit où en est un projet."""
    return f"Projet #{project_id}"


class RecordingToolbox(Toolbox):
    def __init__(self) -> None:
        self.consulted: list[tuple[str, dict[str, Any]]] = []

    @property
    def tools(self) -> Sequence[Tool]:
        return [project_brief]

    async def consult(self, tool: str, arguments: Mapping[str, Any]) -> Consultation:
        self.consulted.append((tool, dict(arguments)))
        return Consultation(tool, dict(arguments), f"Lecture de {tool}")


class ScriptedModels:
    """Hands back the responses it was given, in order, and keeps what it was sent."""

    def __init__(self, responses: list[types.GenerateContentResponse | Exception]):
        self._responses = responses
        self.sent: list[list[types.Content]] = []
        self.configs: list[Any] = []

    async def generate_content(
        self, *, model: str, contents: list[types.Content], config: Any
    ) -> types.GenerateContentResponse:
        self.sent.append(list(contents))
        self.configs.append(config)
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class ScriptedClient:
    def __init__(self, models: ScriptedModels) -> None:
        self.aio = type("Aio", (), {"models": models})()


def written(
    text: str, prompt: int = 100, out: int = 20
) -> types.GenerateContentResponse:
    return types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(role="model", parts=[types.Part(text=text)]),
                finish_reason=types.FinishReason.STOP,
            )
        ],
        usage_metadata=types.GenerateContentResponseUsageMetadata(
            prompt_token_count=prompt,
            candidates_token_count=out,
            thoughts_token_count=5,
        ),
    )


def asking_for(tool: str, **arguments: Any) -> types.GenerateContentResponse:
    return types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            function_call=types.FunctionCall(name=tool, args=arguments)
                        )
                    ],
                ),
                finish_reason=types.FinishReason.STOP,
            )
        ],
        usage_metadata=types.GenerateContentResponseUsageMetadata(
            prompt_token_count=80, candidates_token_count=10, thoughts_token_count=0
        ),
    )


def asking_for_many(count: int) -> types.GenerateContentResponse:
    """One round asking for the same tool on `count` projects at once."""
    response = asking_for("project_brief", project_id=1)
    assert response.candidates and response.candidates[0].content
    response.candidates[0].content.parts = [
        types.Part(
            function_call=types.FunctionCall(
                name="project_brief", args={"project_id": n}
            )
        )
        for n in range(count)
    ]
    return response


def an_answerer(
    *responses: types.GenerateContentResponse | Exception,
) -> tuple[GeminiAnswerer, ScriptedModels, RecordingToolbox]:
    models = ScriptedModels(list(responses))
    toolbox = RecordingToolbox()
    answerer = GeminiAnswerer(
        api_key="key",
        model="gemini-test",
        toolbox=toolbox,
        client=ScriptedClient(models),  # type: ignore[arg-type]
    )
    return answerer, models, toolbox


def texts(content: types.Content) -> list[str]:
    return [part.text for part in content.parts or [] if part.text]


async def test_without_a_key_there_is_nothing_to_ask() -> None:
    answerer = GeminiAnswerer(
        api_key="", model="gemini-test", toolbox=RecordingToolbox()
    )

    assert not answerer.is_available
    missed = await answerer.answer(Conversation.opened(1), "Question ?", None)
    assert isinstance(missed, Unanswered)


async def test_an_answer_written_straight_away_is_handed_back() -> None:
    answerer, _, toolbox = an_answerer(written("Ganesh ne parle que des projets."))

    answer = await answerer.answer(Conversation.opened(1), "Quel temps fait-il ?", None)

    assert isinstance(answer, Answer)
    assert answer.text == "Ganesh ne parle que des projets."
    assert answer.consultations == ()
    assert answer.model == "gemini-test"
    assert (answer.input_tokens, answer.output_tokens) == (100, 25)
    assert toolbox.consulted == []


async def test_a_tool_asked_for_is_consulted_and_its_reading_handed_back() -> None:
    answerer, models, toolbox = an_answerer(
        asking_for("project_brief", project_id=7),
        written("WAATcher est en développement.", prompt=300, out=30),
    )

    answer = await answerer.answer(Conversation.opened(1), "Où en est-il ?", 7)

    assert isinstance(answer, Answer)
    assert answer.text == "WAATcher est en développement."
    assert toolbox.consulted == [("project_brief", {"project_id": 7})]
    assert answer.consultations == (
        Consultation("project_brief", {"project_id": 7}, "Lecture de project_brief"),
    )
    assert (answer.input_tokens, answer.output_tokens) == (380, 45)

    handed_back = models.sent[1][-1].parts or []
    assert handed_back[0].function_response is not None
    assert handed_back[0].function_response.response == {
        "result": "Lecture de project_brief"
    }


async def test_the_model_answers_without_reasoning_at_length() -> None:
    """Measured on the real model: same answers, a third faster, a fifth the tokens."""
    answerer, models, _ = an_answerer(written("Réponse."))

    await answerer.answer(Conversation.opened(1), "Question ?", None)

    assert models.configs[0].thinking_config.thinking_budget == 0


async def test_the_question_says_which_project_is_open() -> None:
    answerer, models, _ = an_answerer(written("Réponse."))

    await answerer.answer(Conversation.opened(1), "Où en est-il ?", 7)

    assert "#7" in texts(models.sent[0][-1])[0]


async def test_the_conversation_so_far_goes_before_the_question() -> None:
    conversation = Conversation.opened(1)
    conversation.record(
        "Où en est WAATcher ?",
        Answer("En développement.", (), "gemini-test", 1, 1, 1),
        project_id=None,
        asked_at=datetime(2026, 10, 10, tzinfo=UTC),
    )
    answerer, models, _ = an_answerer(written("Réponse."))

    await answerer.answer(conversation, "Et depuis quinze jours ?", None)

    sent = models.sent[0]
    assert [content.role for content in sent] == ["user", "model", "user"]
    assert texts(sent[0]) == ["Où en est WAATcher ?"]
    assert texts(sent[1]) == ["En développement."]
    assert texts(sent[2]) == ["Et depuis quinze jours ?"]


async def test_what_the_tools_read_earlier_goes_back_with_its_question() -> None:
    """A follow-up — « et ses lots ? » — is answered from what was already read."""
    conversation = Conversation.opened(1)
    conversation.record(
        "Où en est EDIT ?",
        Answer(
            "EDIT est en service.",
            (
                Consultation(
                    "project_brief", {"project_id": 85}, "EDIT (#85) — projet."
                ),
            ),
            "gemini-test",
            1,
            1,
            1,
        ),
        project_id=None,
        asked_at=datetime(2026, 10, 10, tzinfo=UTC),
    )
    answerer, models, _ = an_answerer(written("Réponse."))

    await answerer.answer(conversation, "Et ses lots ?", None)

    asked_before = texts(models.sent[0][0])
    assert asked_before[0] == "Où en est EDIT ?"
    assert "project_brief" in asked_before[1]
    assert '"project_id": 85' in asked_before[1]
    assert "EDIT (#85) — projet." in asked_before[1]
    assert texts(models.sent[0][1]) == ["EDIT est en service."]


async def test_a_model_that_keeps_asking_is_made_to_answer_with_what_it_read() -> None:
    """Five rounds read, then one more without tools: an answer, not a 503."""
    answerer, models, toolbox = an_answerer(
        *(asking_for("project_brief", project_id=7) for _ in range(MAX_ROUNDS)),
        written("WAATcher est en service ; ses lots n'ont pas pu être lus."),
    )

    answer = await answerer.answer(Conversation.opened(1), "Question ?", None)

    assert isinstance(answer, Answer)
    assert answer.text == "WAATcher est en service ; ses lots n'ont pas pu être lus."
    assert len(toolbox.consulted) == MAX_ROUNDS
    assert len(answer.consultations) == MAX_ROUNDS


async def test_the_closing_round_offers_no_tool_and_says_why() -> None:
    """No tool to call, and no call to imitate: what was read goes back as text."""
    answerer, models, _ = an_answerer(
        *(asking_for("project_brief", project_id=7) for _ in range(MAX_ROUNDS)),
        written("Réponse."),
    )

    await answerer.answer(Conversation.opened(1), "Question ?", None)

    *rounds, closing = models.configs
    assert all(config.tools for config in rounds)
    assert closing.tools is None
    closing_sent = models.sent[-1]
    assert not any(
        part.function_call or part.function_response
        for content in closing_sent
        for part in content.parts or []
    )
    last = closing_sent[-1]
    assert last.role == "user" and last.parts
    assert "Question ?" in (last.parts[0].text or "")
    assert "Lecture de project_brief" in (last.parts[1].text or "")
    assert last.parts[-1].text == ENOUGH


async def test_a_closing_round_that_writes_nothing_says_it_was_cut_short() -> None:
    answerer, _, _ = an_answerer(
        *(asking_for("project_brief", project_id=7) for _ in range(MAX_ROUNDS)),
        written(""),
    )

    missed = await answerer.answer(Conversation.opened(1), "Question ?", None)

    assert isinstance(missed, Unanswered)
    assert missed.reason is WhyUnanswered.CUT_SHORT
    assert len(missed.consultations) == MAX_ROUNDS


async def test_a_model_asking_still_once_made_to_answer_says_so() -> None:
    answerer, _, _ = an_answerer(
        *(asking_for("project_brief", project_id=7) for _ in range(MAX_ROUNDS + 1)),
    )

    missed = await answerer.answer(Conversation.opened(1), "Question ?", None)

    assert isinstance(missed, Unanswered)
    assert missed.reason is WhyUnanswered.KEPT_ASKING
    assert missed.input_tokens > 0


async def test_a_question_reads_no_more_than_its_share_of_the_register() -> None:
    """Rounds are capped, and so is what one round may ask for."""
    answerer, models, toolbox = an_answerer(
        asking_for_many(MAX_CONSULTATIONS + 5), written("Réponse.")
    )

    answer = await answerer.answer(Conversation.opened(1), "Tous les projets ?", None)

    assert len(toolbox.consulted) == MAX_CONSULTATIONS
    assert isinstance(answer, Answer)
    refused = [c for c in answer.consultations if c not in toolbox_readings(toolbox)]
    assert len(refused) == 5
    assert all("Assez de lectures" in c.result for c in refused)


def toolbox_readings(toolbox: RecordingToolbox) -> list[Consultation]:
    return [
        Consultation(tool, arguments, f"Lecture de {tool}")
        for tool, arguments in toolbox.consulted
    ]


async def test_a_provider_that_fails_keeps_what_was_read_before() -> None:
    """What the tools read before it went wrong is what explains the failure."""
    answerer, _, _ = an_answerer(
        asking_for("project_brief", project_id=7), RuntimeError("quota exceeded")
    )

    missed = await answerer.answer(Conversation.opened(1), "Question ?", None)

    assert isinstance(missed, Unanswered)
    assert missed.reason is WhyUnanswered.PROVIDER_FAILED
    assert [held.tool for held in missed.consultations] == ["project_brief"]


async def test_an_answer_cut_short_is_not_handed_back() -> None:
    cut = written("WAATcher est en")
    assert cut.candidates is not None
    cut.candidates[0].finish_reason = types.FinishReason.MAX_TOKENS
    answerer, _, _ = an_answerer(cut)

    missed = await answerer.answer(Conversation.opened(1), "Question ?", None)
    assert isinstance(missed, Unanswered)
    assert missed.reason is WhyUnanswered.CUT_SHORT
