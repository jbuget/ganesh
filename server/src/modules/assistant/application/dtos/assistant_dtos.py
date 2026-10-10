"""What the assistant is asked, and what it hands back."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.assistant.domain.entities.conversation import Conversation
from src.modules.assistant.domain.entities.exchange import Answer, Exchange, Verdict


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
