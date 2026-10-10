"""Asking Gemini, and letting it read the tools until it can answer.

The same model and the same key as the gazette — `GEMINI_MODEL`,
`GEMINI_API_KEY` — and the same contract: no key, no answer, nothing broken.

The loop is written by hand rather than left to the SDK's automatic calling,
for two reasons: every reading has to be kept with the answer, which is what
makes an exchange studiable afterwards, and the number of rounds has to be
bounded, a model that keeps asking being a bill that keeps growing.

A follow-up goes with the whole conversation so far: each earlier question,
what the tools read to answer it, and the answer. The readings ride with their
question as plain text rather than as the function calls they were: a call
replayed from a past turn would need the signature the model gave it then,
which nothing keeps. Five turns of readings is a few thousand tokens — the
price of « et ses lots ? » being answered from what was already read.
"""

import json
import logging
import time

from google import genai
from google.genai import types

from src.assistant.answerer import Answerer
from src.assistant.prompt import framed, instructions
from src.assistant.toolbox import Toolbox
from src.modules.assistant.domain.entities.conversation import Conversation
from src.modules.assistant.domain.entities.exchange import Answer, Consultation
from src.shared.utils import clock

logger = logging.getLogger(__name__)

#: How many times the model may go back to the tools before it must have
#: answered. « Où en est X ? » takes two: find the project, read its sheet.
MAX_ROUNDS = 5

#: How many readings one question may cost, whatever the rounds. A round may
#: ask for many tools at once, and each brief reads every lot of its project:
#: capping rounds alone would leave one question able to read the register
#: whole. Past this, the model is told it has read enough, and answers.
MAX_CONSULTATIONS = 12

#: What a reading past the cap says instead.
ENOUGH = (
    "Assez de lectures pour une seule question : réponds avec ce qui a déjà été "
    "lu, et dis ce qui n'a pas pu l'être."
)

#: How long one call to the model may take, in milliseconds. A provider that
#: hangs must not hold the request — and the connection behind it — for ever.
TIMEOUT_MS = 30_000

#: An answer is a few sentences, with room to spare should the model reason
#: anyway.
MAX_OUTPUT_TOKENS = 4000

#: No reasoning before answering. Measured on « où en est WAATcher ? » against
#: the production register: the same answers, read from the same tools, in a
#: third less time and a fifth of the output tokens. The tools have already
#: done the thinking that counts. A model that ignored it — the gazette's
#: adapter saw one do so — would only be slower, never wrong.
THINKING_BUDGET = 0

#: Low: the answer is a reading of the tools, not a variation on them.
TEMPERATURE = 0.2


class GeminiAnswerer(Answerer):
    def __init__(
        self,
        api_key: str,
        model: str,
        toolbox: Toolbox,
        client: genai.Client | None = None,
    ) -> None:
        self._model = model
        self._toolbox = toolbox
        self._client = client or (
            genai.Client(
                api_key=api_key, http_options=types.HttpOptions(timeout=TIMEOUT_MS)
            )
            if api_key
            else None
        )

    @property
    def is_available(self) -> bool:
        return self._client is not None

    async def answer(
        self, conversation: Conversation, question: str, project_id: int | None
    ) -> Answer | None:
        if self._client is None:
            return None

        try:
            return await self._converse(conversation, question, project_id)
        except Exception:
            # Whatever went wrong — the provider, or a bug of ours — the person
            # is told the assistant could not answer; the trace is for us.
            logger.exception("Gemini did not answer the assistant.")
            return None

    async def _converse(
        self, conversation: Conversation, question: str, project_id: int | None
    ) -> Answer | None:
        assert self._client is not None
        started = time.monotonic()
        contents = [
            *_history(conversation),
            _said("user", framed(question, project_id)),
        ]
        consultations: list[Consultation] = []
        input_tokens = output_tokens = 0

        for _ in range(MAX_ROUNDS):
            response = await self._client.aio.models.generate_content(
                model=self._model, contents=contents, config=self._config()
            )
            input_tokens += _input_tokens(response)
            output_tokens += _output_tokens(response)

            calls = response.function_calls
            if not calls:
                text = response.text
                if not _finished(response) or not text:
                    logger.warning("Gemini was cut short or wrote nothing.")
                    return None
                return Answer(
                    text=text.strip(),
                    consultations=tuple(consultations),
                    model=self._model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    elapsed_ms=round((time.monotonic() - started) * 1000),
                )

            contents.append(_asked(response))
            readings: list[Consultation] = []
            for call in calls:
                name, arguments = call.name or "", dict(call.args or {})
                if len(consultations) + len(readings) < MAX_CONSULTATIONS:
                    readings.append(await self._toolbox.consult(name, arguments))
                else:
                    readings.append(Consultation(name, arguments, ENOUGH))
            consultations.extend(readings)
            contents.append(_read(readings))

        logger.warning("Gemini was still asking for tools after %s rounds.", MAX_ROUNDS)
        return None

    def _config(self) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            system_instruction=instructions(clock.today()),
            tools=[
                types.Tool(
                    function_declarations=[
                        types.FunctionDeclaration.from_callable_with_api_option(
                            callable=tool, api_option="GEMINI_API"
                        )
                        for tool in self._toolbox.tools
                    ]
                )
            ],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
            thinking_config=types.ThinkingConfig(thinking_budget=THINKING_BUDGET),
            temperature=TEMPERATURE,
            max_output_tokens=MAX_OUTPUT_TOKENS,
        )


def _history(conversation: Conversation) -> list[types.Content]:
    contents: list[types.Content] = []
    for exchange in conversation.exchanges:
        asked = [types.Part(text=framed(exchange.question, exchange.project_id))]
        if exchange.answer.consultations:
            asked.append(types.Part(text=_readings(exchange.answer.consultations)))
        contents.append(types.Content(role="user", parts=asked))
        contents.append(_said("model", exchange.answer.text))
    return contents


def _readings(consultations: tuple[Consultation, ...]) -> str:
    """What the tools read for an earlier question, as the model was shown it."""
    return "(Pour répondre à cette question, les outils ont rendu :)\n" + "\n\n".join(
        f"{reading.tool}({json.dumps(reading.arguments, ensure_ascii=False)}) :\n"
        f"{reading.result}"
        for reading in consultations
    )


def _said(role: str, text: str) -> types.Content:
    return types.Content(role=role, parts=[types.Part(text=text)])


def _asked(response: types.GenerateContentResponse) -> types.Content:
    """What the model asked for, sent back so that it recognises its readings."""
    candidates = response.candidates or []
    content = candidates[0].content if candidates else None
    return content or types.Content(role="model", parts=[])


def _read(readings: list[Consultation]) -> types.Content:
    return types.Content(
        role="user",
        parts=[
            types.Part.from_function_response(
                name=reading.tool, response={"result": reading.result}
            )
            for reading in readings
        ],
    )


def _finished(response: types.GenerateContentResponse) -> bool:
    """Whether the model stopped because it had finished, not because it ran out."""
    candidates = response.candidates or []
    if not candidates:
        return False
    return candidates[0].finish_reason is types.FinishReason.STOP


def _input_tokens(response: types.GenerateContentResponse) -> int:
    usage = response.usage_metadata
    return (usage.prompt_token_count or 0) if usage else 0


def _output_tokens(response: types.GenerateContentResponse) -> int:
    """What is billed as output: the answer, and the reasoning that preceded it."""
    usage = response.usage_metadata
    if usage is None:
        return 0
    return (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)
