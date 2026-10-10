"""The assistant, studied: every exchange kept, read by an administrator.

Its own router, under the administration's prefix: the panel's routes answer
whoever asked, and somebody else's conversation reads there as nothing; these
read them all, which is why `get_admin` is the only door they open on.
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.assistant.application.dtos.assistant_dtos import AnnotateCommand
from src.modules.assistant.application.use_cases.annotate_exchange import (
    AnnotateExchangeUseCase,
)
from src.modules.assistant.application.use_cases.export_exchanges import (
    ExportExchangesUseCase,
)
from src.modules.assistant.application.use_cases.list_conversations import (
    ListConversationsUseCase,
)
from src.modules.assistant.application.use_cases.read_conversation import (
    ReadConversationUseCase,
)
from src.modules.assistant.application.use_cases.read_indicators import (
    ReadIndicatorsUseCase,
)
from src.modules.assistant.domain.repositories.exchange_archive import (
    ExchangeFilter,
    Judgement,
)
from src.modules.assistant.presentation.api.exports import (
    MEDIA_TYPES,
    ExportFormat,
    written_as,
)
from src.modules.assistant.presentation.api.mappers.study_mapper import (
    to_conversation_detail_response,
    to_conversation_page_response,
    to_exported_exchanges,
    to_indicators_response,
    to_studied_exchange_response,
)
from src.modules.assistant.presentation.api.schemas.study_schemas import (
    AnnotateRequest,
    AssistantIndicatorsResponse,
    ConversationDetailResponse,
    ConversationPageResponse,
    StudiedExchangeResponse,
)
from src.modules.assistant.presentation.dependencies import (
    get_annotate_exchange_use_case,
    get_export_exchanges_use_case,
    get_list_conversations_use_case,
    get_read_conversation_use_case,
    get_read_indicators_use_case,
)
from src.modules.auth.presentation.dependencies import get_admin
from src.modules.users.domain.entities.user import User
from src.shared.utils import clock

router = APIRouter(prefix="/admin/assistant", tags=["admin"])


def kept_by(
    from_day: date | None = Query(
        default=None,
        description="Only what was asked on this day or after, Paris time.",
    ),
    to_day: date | None = Query(
        default=None,
        description="Only what was asked on this day or before, Paris time.",
    ),
    asker_id: int | None = Query(
        default=None, description="Only what this person asked."
    ),
    judgement: Judgement | None = Query(
        default=None, description="Only what whoever asked said of the answer."
    ),
) -> ExchangeFilter:
    """The same four criteria for every reading, so that they all agree."""
    return ExchangeFilter(
        since=None if from_day is None else clock.opens(from_day),
        until=None if to_day is None else clock.closes(to_day),
        asker_id=asker_id,
        judgement=judgement,
    )


@router.get(
    "/conversations",
    response_model=ConversationPageResponse,
    operation_id="listAssistantConversations",
)
async def list_conversations(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    kept: ExchangeFilter = Depends(kept_by),
    _: User = Depends(get_admin),
    use_case: ListConversationsUseCase = Depends(get_list_conversations_use_case),
) -> ConversationPageResponse:
    """The conversations holding an exchange the filter keeps, latest first."""
    return to_conversation_page_response(await use_case.execute(kept, limit, offset))


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
    operation_id="readAssistantConversation",
)
async def read_conversation(
    conversation_id: UUID,
    _: User = Depends(get_admin),
    use_case: ReadConversationUseCase = Depends(get_read_conversation_use_case),
) -> ConversationDetailResponse:
    """A conversation whole, with what every tool read back."""
    return to_conversation_detail_response(await use_case.execute(conversation_id))


@router.get(
    "/indicators",
    response_model=AssistantIndicatorsResponse,
    operation_id="readAssistantIndicators",
)
async def read_indicators(
    kept: ExchangeFilter = Depends(kept_by),
    _: User = Depends(get_admin),
    use_case: ReadIndicatorsUseCase = Depends(get_read_indicators_use_case),
) -> AssistantIndicatorsResponse:
    """What the exchanges the filter keeps say about the assistant."""
    return to_indicators_response(await use_case.execute(kept))


@router.get(
    "/exchanges/export",
    response_class=Response,
    operation_id="exportAssistantExchanges",
    responses={
        200: {
            "content": {media: {} for media in MEDIA_TYPES.values()},
            "description": "The exchanges, as a file to save.",
        }
    },
)
async def export_exchanges(
    written_in: ExportFormat = Query(default=ExportFormat.CSV, alias="format"),
    kept: ExchangeFilter = Depends(kept_by),
    _: User = Depends(get_admin),
    use_case: ExportExchangesUseCase = Depends(get_export_exchanges_use_case),
) -> Response:
    """Every exchange the filter keeps, oldest first, as a file."""
    exported = to_exported_exchanges(await use_case.execute(kept))
    return Response(
        content=written_as(exported, written_in),
        media_type=MEDIA_TYPES[written_in],
        headers={
            "Content-Disposition": (
                f'attachment; filename="assistant-{clock.today().isoformat()}.{written_in}"'
            )
        },
    )


@router.put(
    "/exchanges/{exchange_id}/annotation",
    response_model=StudiedExchangeResponse,
    operation_id="annotateAssistantExchange",
)
async def annotate_exchange(
    exchange_id: int,
    payload: AnnotateRequest,
    current_user: User = Depends(get_admin),
    use_case: AnnotateExchangeUseCase = Depends(get_annotate_exchange_use_case),
    session: AsyncSession = Depends(get_db),
) -> StudiedExchangeResponse:
    """Says why an answer came out as it did, replacing any earlier reading."""
    assert current_user.id is not None
    annotated = await use_case.execute(
        AnnotateCommand(
            exchange_id=exchange_id,
            annotator_id=current_user.id,
            cause=payload.cause,
            note=payload.note,
        )
    )
    await session.commit()
    return to_studied_exchange_response(annotated)
