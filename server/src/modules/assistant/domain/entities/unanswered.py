"""A question the assistant could not answer, kept to study why.

Apart from the exchanges on purpose: a question nobody answered carries no
answer, no verdict and no annotation, and takes none of the five places of its
conversation — asking again is the same question, not the next one. An entity
defined by what it does not carry would be in the wrong table.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from src.modules.assistant.domain.entities.exchange import Consultation


class WhyUnanswered(StrEnum):
    """Why no answer came back."""

    #: The provider refused or failed: a quota, a timeout, an error of ours.
    PROVIDER_FAILED = "provider_failed"
    #: The model stopped before it had finished, or wrote nothing.
    CUT_SHORT = "cut_short"
    #: Made to answer, the model asked for tools still.
    KEPT_ASKING = "kept_asking"


@dataclass(frozen=True)
class Unanswered:
    """What came back instead of an answer, and what it cost to get there."""

    reason: WhyUnanswered
    consultations: tuple[Consultation, ...]
    model: str
    input_tokens: int
    output_tokens: int
    elapsed_ms: int


@dataclass
class UnansweredQuestion:
    conversation_id: UUID
    asker_id: int
    question: str
    unanswered: Unanswered
    #: The project open on screen when the question was asked, if any.
    project_id: int | None
    asked_at: datetime
    id: int | None = None
