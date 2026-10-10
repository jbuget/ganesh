"""The route that asks the assistant a question.

Reached from a panel the sidebar does not announce, opened with ⌘J. Anybody
who may write into Ganesh may ask; a guest never comes this far. Asking writes
— the exchange is kept, to study the assistant — so the question goes through
the door a guest cannot come through.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.assistant.answerer import Answerer
from src.assistant.asking import ask
from src.assistant.dependencies import get_answerer
from src.core.database import get_db
from src.modules.assistant.application.dtos.assistant_dtos import AskCommand
from src.modules.assistant.application.use_cases.admit_question import (
    AdmitQuestionUseCase,
)
from src.modules.assistant.application.use_cases.record_exchange import (
    RecordExchangeUseCase,
)
from src.modules.assistant.application.use_cases.record_unanswered import (
    RecordUnansweredUseCase,
)
from src.modules.assistant.domain.entities.unanswered import UnansweredQuestion
from src.modules.assistant.presentation.api.mappers.assistant_mapper import (
    to_exchange_response,
)
from src.modules.assistant.presentation.api.schemas.assistant_schemas import (
    AskRequest,
    ExchangeResponse,
)
from src.modules.assistant.presentation.dependencies import (
    get_admit_question_use_case,
    get_record_exchange_use_case,
    get_record_unanswered_use_case,
)
from src.modules.auth.presentation.dependencies import get_contributor
from src.modules.users.domain.entities.user import User
from src.shared.exceptions.domain_exceptions import ServiceUnavailableError

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post(
    "/exchanges",
    response_model=ExchangeResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="askAssistant",
)
async def ask_assistant(
    payload: AskRequest,
    current_user: User = Depends(get_contributor),
    admit: AdmitQuestionUseCase = Depends(get_admit_question_use_case),
    answerer: Answerer = Depends(get_answerer),
    record: RecordExchangeUseCase = Depends(get_record_exchange_use_case),
    record_unanswered: RecordUnansweredUseCase = Depends(
        get_record_unanswered_use_case
    ),
    session: AsyncSession = Depends(get_db),
) -> ExchangeResponse:
    """Asks a question. Without a conversation, it opens one."""
    assert current_user.id is not None
    asked = await ask(
        AskCommand(
            asker_id=current_user.id,
            question=payload.question,
            conversation_id=payload.conversation_id,
            project_id=payload.project_id,
        ),
        admit=admit,
        answerer=answerer,
        record=record,
        record_unanswered=record_unanswered,
    )
    # Committed before anything is said: an unanswered question is kept to
    # study it, and the refusal below must not take it with it.
    await session.commit()
    if isinstance(asked, UnansweredQuestion):
        raise ServiceUnavailableError("The assistant could not answer.")
    return to_exchange_response(asked)
