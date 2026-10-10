"""From the exchanges kept to what an administrator reads of them."""

from src.modules.assistant.application.dtos.assistant_dtos import (
    AssistantIndicators,
    ExchangeExport,
)
from src.modules.assistant.domain.entities.conversation import Conversation
from src.modules.assistant.domain.entities.exchange import (
    Consultation,
    Exchange,
    Verdict,
)
from src.modules.assistant.domain.entities.unanswered import UnansweredQuestion
from src.modules.assistant.domain.repositories.exchange_archive import (
    ConversationPage,
    UnansweredPage,
)
from src.modules.assistant.presentation.api.schemas.study_schemas import (
    AnnotationResponse,
    AssistantIndicatorsResponse,
    CauseCountResponse,
    ConsultationResponse,
    ConversationDetailResponse,
    ConversationPageResponse,
    ConversationSummaryResponse,
    ExportedExchangeResponse,
    StudiedExchangeResponse,
    ToolCountResponse,
    UnansweredPageResponse,
    UnansweredQuestionResponse,
)


def _consultations(
    consultations: tuple[Consultation, ...],
) -> list[ConsultationResponse]:
    return [
        ConsultationResponse(
            tool=held.tool, arguments=held.arguments, result=held.result
        )
        for held in consultations
    ]


def to_studied_exchange_response(exchange: Exchange) -> StudiedExchangeResponse:
    assert exchange.id is not None
    annotation = exchange.annotation
    return StudiedExchangeResponse(
        id=exchange.id,
        conversation_id=exchange.conversation_id,
        rank=exchange.rank,
        asker_id=exchange.asker_id,
        project_id=exchange.project_id,
        asked_at=exchange.asked_at,
        question=exchange.question,
        answer=exchange.answer.text,
        consultations=_consultations(exchange.answer.consultations),
        model=exchange.answer.model,
        input_tokens=exchange.answer.input_tokens,
        output_tokens=exchange.answer.output_tokens,
        elapsed_ms=exchange.answer.elapsed_ms,
        verdict=exchange.verdict,
        annotation=(
            AnnotationResponse(
                cause=annotation.cause,
                note=annotation.note,
                annotated_by=annotation.annotated_by,
                annotated_at=annotation.annotated_at,
            )
            if annotation is not None
            else None
        ),
    )


def _summary(conversation: Conversation) -> ConversationSummaryResponse:
    return ConversationSummaryResponse(
        id=conversation.id,
        asker_id=conversation.asker_id,
        started_at=conversation.started_at,
        last_asked_at=conversation.last_asked_at,
        first_question=conversation.first_question,
        exchange_count=len(conversation.exchanges),
        helpful=conversation.judged(Verdict.HELPFUL),
        unhelpful=conversation.judged(Verdict.UNHELPFUL),
        annotated=conversation.annotated,
    )


def to_conversation_page_response(page: ConversationPage) -> ConversationPageResponse:
    return ConversationPageResponse(
        total=page.total,
        conversations=[_summary(held) for held in page.conversations],
    )


def to_conversation_detail_response(
    conversation: Conversation,
) -> ConversationDetailResponse:
    return ConversationDetailResponse(
        id=conversation.id,
        asker_id=conversation.asker_id,
        exchanges=[
            to_studied_exchange_response(held) for held in conversation.exchanges
        ],
    )


def to_indicators_response(read: AssistantIndicators) -> AssistantIndicatorsResponse:
    counted = read.indicators
    return AssistantIndicatorsResponse(
        kept_since=read.kept_since,
        questions=counted.questions,
        unanswered=read.unanswered,
        conversations=counted.conversations,
        askers=counted.askers,
        helpful=counted.helpful,
        unhelpful=counted.unhelpful,
        unjudged=counted.unjudged,
        causes=[
            CauseCountResponse(cause=cause, count=count)
            for cause, count in counted.causes.items()
        ],
        unannotated=counted.unannotated,
        median_elapsed_ms=counted.median_elapsed_ms,
        p95_elapsed_ms=counted.p95_elapsed_ms,
        input_tokens=counted.input_tokens,
        output_tokens=counted.output_tokens,
        tools=[
            ToolCountResponse(tool=tool, count=count) for tool, count in counted.tools
        ],
    )


def to_exported_exchanges(export: ExchangeExport) -> list[ExportedExchangeResponse]:
    exported = []
    for exchange in export.exchanges:
        asker = export.askers.get(exchange.asker_id)
        exported.append(
            ExportedExchangeResponse(
                **to_studied_exchange_response(exchange).model_dump(),
                asker_name=asker.label if asker else None,
                asker_email=asker.email if asker else None,
            )
        )
    return exported


def _unanswered(question: UnansweredQuestion) -> UnansweredQuestionResponse:
    assert question.id is not None
    unanswered = question.unanswered
    return UnansweredQuestionResponse(
        id=question.id,
        conversation_id=question.conversation_id,
        asker_id=question.asker_id,
        project_id=question.project_id,
        asked_at=question.asked_at,
        question=question.question,
        reason=unanswered.reason,
        consultations=_consultations(unanswered.consultations),
        model=unanswered.model,
        input_tokens=unanswered.input_tokens,
        output_tokens=unanswered.output_tokens,
        elapsed_ms=unanswered.elapsed_ms,
    )


def to_unanswered_page_response(page: UnansweredPage) -> UnansweredPageResponse:
    return UnansweredPageResponse(
        total=page.total, questions=[_unanswered(held) for held in page.questions]
    )
