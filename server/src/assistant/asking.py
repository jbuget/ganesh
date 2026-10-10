"""Asking: the question admitted, put to the model, and the exchange kept.

The three steps a way in strings together, as a terminal client strings
tools: each is a use case of the module or the model itself, and none of them
calls another. Nothing is decided here that a use case decides.
"""

from src.assistant.answerer import Answerer
from src.modules.assistant.application.dtos.assistant_dtos import (
    AskCommand,
    AskResult,
    RecordCommand,
)
from src.modules.assistant.application.use_cases.admit_question import (
    AdmitQuestionUseCase,
)
from src.modules.assistant.application.use_cases.record_exchange import (
    RecordExchangeUseCase,
)
from src.shared.exceptions.domain_exceptions import ServiceUnavailableError


async def ask(
    command: AskCommand,
    admit: AdmitQuestionUseCase,
    answerer: Answerer,
    record: RecordExchangeUseCase,
) -> AskResult:
    """The answer to one question, kept — or the reason there is none."""
    if not answerer.is_available:
        raise ServiceUnavailableError("No model is configured for the assistant.")

    admitted = await admit.execute(command)
    answer = await answerer.answer(
        admitted.conversation, admitted.question, admitted.project_id
    )
    if answer is None:
        raise ServiceUnavailableError("The assistant could not answer.")
    return await record.execute(RecordCommand(admitted=admitted, answer=answer))
