"""What an administrator reads of the exchanges kept, to study the assistant.

People and projects go over as identifiers, the screen already holding their
names; an export names them, a file having nobody to ask.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from src.modules.assistant.domain.entities.exchange import Cause, Verdict
from src.modules.assistant.domain.entities.unanswered import WhyUnanswered


class ConsultationResponse(BaseModel):
    tool: str
    arguments: dict[str, Any]
    #: What the tool read back, word for word: what the model was handed.
    result: str


class AnnotationResponse(BaseModel):
    cause: Cause
    note: str | None
    annotated_by: int | None
    annotated_at: datetime


class StudiedExchangeResponse(BaseModel):
    id: int
    conversation_id: UUID
    rank: int
    asker_id: int
    #: The project open on screen when the question was asked, if any.
    project_id: int | None
    asked_at: datetime
    question: str
    answer: str
    consultations: list[ConsultationResponse]
    model: str
    input_tokens: int
    output_tokens: int
    elapsed_ms: int
    verdict: Verdict | None
    annotation: AnnotationResponse | None


class ConversationSummaryResponse(BaseModel):
    id: UUID
    asker_id: int
    started_at: datetime
    last_asked_at: datetime
    first_question: str
    exchange_count: int
    helpful: int
    unhelpful: int
    annotated: int


class ConversationPageResponse(BaseModel):
    #: Every conversation the filter holds, not only the page.
    total: int
    conversations: list[ConversationSummaryResponse]


class ConversationDetailResponse(BaseModel):
    id: UUID
    asker_id: int
    exchanges: list[StudiedExchangeResponse]


class CauseCountResponse(BaseModel):
    cause: Cause
    count: int


class ToolCountResponse(BaseModel):
    tool: str
    count: int


class AssistantIndicatorsResponse(BaseModel):
    #: When the oldest exchange still kept was asked, if any is.
    kept_since: datetime | None
    questions: int
    #: Beside the questions answered, not among them.
    unanswered: int
    conversations: int
    askers: int
    helpful: int
    unhelpful: int
    unjudged: int
    #: Every cause, in the order the domain names them, zero included.
    causes: list[CauseCountResponse]
    unannotated: int
    #: Absent when nobody asked: zero would read as an instant answer.
    median_elapsed_ms: int | None
    p95_elapsed_ms: int | None
    input_tokens: int
    output_tokens: int
    #: Most asked first.
    tools: list[ToolCountResponse]


class AnnotateRequest(BaseModel):
    cause: Cause
    note: str | None = None


class ExportedExchangeResponse(StudiedExchangeResponse):
    asker_name: str | None
    asker_email: str | None


class UnansweredQuestionResponse(BaseModel):
    id: int
    conversation_id: UUID
    asker_id: int
    project_id: int | None
    asked_at: datetime
    question: str
    reason: WhyUnanswered
    consultations: list[ConsultationResponse]
    model: str
    input_tokens: int
    output_tokens: int
    elapsed_ms: int


class UnansweredPageResponse(BaseModel):
    #: Every question the filter holds, not only the page.
    total: int
    questions: list[UnansweredQuestionResponse]
