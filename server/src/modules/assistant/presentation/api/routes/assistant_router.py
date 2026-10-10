"""The assistant's routes, all but the one that asks.

Asking hands the question to a model and lives in `src.assistant`, the way in
the model belongs to. What stays here is business: what the panel is told
before anybody asks, and the verdict left under an answer — through the door a
guest cannot come through, a verdict being a write.
"""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.assistant.application.dtos.assistant_dtos import JudgeCommand
from src.modules.assistant.application.use_cases.judge_answer import JudgeAnswerUseCase
from src.modules.assistant.application.use_cases.read_assistant import (
    ReadAssistantUseCase,
)
from src.modules.assistant.presentation.api.mappers.assistant_mapper import (
    to_status_response,
)
from src.modules.assistant.presentation.api.schemas.assistant_schemas import (
    AssistantStatusResponse,
    JudgeRequest,
)
from src.modules.assistant.presentation.dependencies import (
    get_judge_answer_use_case,
    get_read_assistant_use_case,
)
from src.modules.auth.presentation.dependencies import get_contributor, get_current_user
from src.modules.users.domain.entities.user import User

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.get("", response_model=AssistantStatusResponse, operation_id="getAssistant")
async def get_assistant(
    _: User = Depends(get_current_user),
    use_case: ReadAssistantUseCase = Depends(get_read_assistant_use_case),
) -> AssistantStatusResponse:
    """Whether a model is configured, and how long a conversation runs."""
    return to_status_response(await use_case.execute())


@router.put(
    "/exchanges/{exchange_id}/verdict",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="judgeAnswer",
)
async def judge_answer(
    exchange_id: int,
    payload: JudgeRequest,
    current_user: User = Depends(get_contributor),
    use_case: JudgeAnswerUseCase = Depends(get_judge_answer_use_case),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Says whether an answer helped. Only whoever asked says it."""
    assert current_user.id is not None
    await use_case.execute(
        JudgeCommand(
            exchange_id=exchange_id, judge_id=current_user.id, verdict=payload.verdict
        )
    )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
