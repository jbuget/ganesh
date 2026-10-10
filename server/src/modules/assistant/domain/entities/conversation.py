"""A conversation with the assistant: five exchanges, then a fresh one.

The cap keeps the model on the question that was asked — a long thread drifts,
and every turn sends the whole of it again — and it lives here rather than in a
component, so that a client that forgot it meets the same refusal.

A conversation belongs to whoever opened it. Nobody carries on somebody else's.
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from src.modules.assistant.domain.entities.exchange import Answer, Exchange, Verdict
from src.modules.assistant.domain.entities.unanswered import (
    Unanswered,
    UnansweredQuestion,
)
from src.shared.exceptions.domain_exceptions import ConflictError, ValidationError

MAX_EXCHANGES = 5

#: A question, not a document to analyse: nothing multimodal, nothing pasted.
MAX_QUESTION_LENGTH = 2000


class ConversationOverError(ConflictError):
    """The conversation has had its five exchanges."""


@dataclass
class Conversation:
    id: UUID
    asker_id: int
    exchanges: list[Exchange] = field(default_factory=list)

    @classmethod
    def opened(cls, asker_id: int) -> "Conversation":
        return cls(id=uuid4(), asker_id=asker_id)

    @property
    def remaining(self) -> int:
        return MAX_EXCHANGES - len(self.exchanges)

    @property
    def first_question(self) -> str:
        """What opened the conversation: what one scans a list of them for."""
        return self.exchanges[0].question

    @property
    def started_at(self) -> datetime:
        return self.exchanges[0].asked_at

    @property
    def last_asked_at(self) -> datetime:
        return self.exchanges[-1].asked_at

    def judged(self, verdict: Verdict) -> int:
        """How many of its answers whoever asked judged so."""
        return sum(exchange.verdict is verdict for exchange in self.exchanges)

    @property
    def annotated(self) -> int:
        """How many of its answers an administrator has read and annotated."""
        return sum(exchange.annotation is not None for exchange in self.exchanges)

    def admit(self, question: str) -> str:
        """The question as it will be asked, or a refusal saying why not."""
        if self.remaining <= 0:
            raise ConversationOverError(
                f"A conversation holds {MAX_EXCHANGES} exchanges; start a new one."
            )
        asked = question.strip()
        if not asked:
            raise ValidationError("A question cannot be empty.")
        if len(asked) > MAX_QUESTION_LENGTH:
            raise ValidationError(
                f"A question holds at most {MAX_QUESTION_LENGTH} characters."
            )
        return asked

    def record(
        self,
        question: str,
        answer: Answer,
        project_id: int | None,
        asked_at: datetime,
    ) -> Exchange:
        exchange = Exchange(
            conversation_id=self.id,
            rank=len(self.exchanges) + 1,
            asker_id=self.asker_id,
            question=question,
            answer=answer,
            project_id=project_id,
            asked_at=asked_at,
        )
        self.exchanges.append(exchange)
        return exchange

    def missed(
        self,
        question: str,
        unanswered: Unanswered,
        project_id: int | None,
        asked_at: datetime,
    ) -> UnansweredQuestion:
        """A question put in this conversation that came back with no answer.

        It takes no place in the conversation: asked again, it is the same
        question, and the five places are for answers.
        """
        return UnansweredQuestion(
            conversation_id=self.id,
            asker_id=self.asker_id,
            question=question,
            unanswered=unanswered,
            project_id=project_id,
            asked_at=asked_at,
        )
