"""A conversation with the assistant: five exchanges, then a fresh one.

The cap keeps the model on the question that was asked — a long thread drifts,
and every turn sends the whole of it again — and it lives here rather than in a
component, so that a client that forgot it meets the same refusal.

A conversation belongs to whoever opened it. Nobody carries on somebody else's.
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from src.modules.assistant.domain.entities.exchange import Answer, Exchange
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
