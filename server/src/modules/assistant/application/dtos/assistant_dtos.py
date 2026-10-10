"""What the assistant is asked, and what it hands back."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.modules.assistant.domain.entities.conversation import Conversation
from src.modules.assistant.domain.entities.exchange import (
    Answer,
    Cause,
    Exchange,
    Verdict,
)
from src.modules.assistant.domain.entities.unanswered import Unanswered
from src.modules.assistant.domain.services.indicators import Indicators
from src.modules.users.domain.entities.user import User


@dataclass(frozen=True)
class AskCommand:
    """A question. Without a conversation, it opens one."""

    asker_id: int
    question: str
    conversation_id: UUID | None = None
    #: The project open on screen, so that « où en est-il ? » has a subject.
    project_id: int | None = None


@dataclass(frozen=True)
class AdmittedQuestion:
    """A question that may be put: the conversation it goes in, as it will be asked."""

    conversation: Conversation
    question: str
    #: The project on screen, once it is known to exist.
    project_id: int | None


@dataclass(frozen=True)
class RecordCommand:
    """An admitted question, and the answer it received."""

    admitted: AdmittedQuestion
    answer: Answer


@dataclass(frozen=True)
class RecordUnansweredCommand:
    """An admitted question, and what came back instead of an answer."""

    admitted: AdmittedQuestion
    unanswered: Unanswered


@dataclass(frozen=True)
class AskResult:
    exchange: Exchange
    #: How many questions the conversation still holds.
    remaining: int


@dataclass(frozen=True)
class JudgeCommand:
    exchange_id: int
    judge_id: int
    verdict: Verdict


@dataclass(frozen=True)
class AssistantStatus:
    """Whether a model is configured, and how long a conversation runs."""

    is_available: bool
    max_exchanges: int


@dataclass(frozen=True)
class AnnotateCommand:
    exchange_id: int
    annotator_id: int
    cause: Cause
    note: str | None


@dataclass(frozen=True)
class AssistantIndicators:
    indicators: Indicators
    #: When the oldest exchange still kept was asked: how far back one can look.
    kept_since: datetime | None
    #: The questions the filter keeps that came back with no answer.
    unanswered: int


@dataclass(frozen=True)
class ExchangeExport:
    exchanges: list[Exchange]
    #: Whoever asked each exchange, by id. An account gone takes its rows with it.
    askers: dict[int, User]
