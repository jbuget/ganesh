"""Assistant schemas.

The answer is the one piece of French the API carries here, because a model
wrote it. Which projects it was read from goes over as identifiers: the panel
already holds their names.
"""

from uuid import UUID

from pydantic import BaseModel, Field

from src.modules.assistant.domain.entities.exchange import Verdict


class AssistantStatusResponse(BaseModel):
    is_available: bool
    max_exchanges: int


class AskRequest(BaseModel):
    question: str
    #: Absent on the first question: asking opens the conversation.
    conversation_id: UUID | None = None
    #: The project open on screen, so that « où en est-il ? » has a subject.
    project_id: int | None = Field(default=None, ge=1)


class ExchangeResponse(BaseModel):
    id: int
    conversation_id: UUID
    rank: int
    #: How many questions the conversation still holds.
    remaining: int
    question: str
    answer: str
    #: The projects the answer was read from, each once, first read first.
    consulted_project_ids: list[int]
    verdict: Verdict | None


class JudgeRequest(BaseModel):
    verdict: Verdict
