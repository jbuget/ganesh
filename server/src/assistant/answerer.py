"""Port for the model that answers.

It is handed the conversation so far and the new question, and hands back an
answer, or what came back instead and why. No answer is a normal outcome — the
provider down, a model cut short, one that kept asking for tools — and the
assistant says so to whoever asked, and keeps the question to study it.
"""

from abc import ABC, abstractmethod

from src.modules.assistant.domain.entities.conversation import Conversation
from src.modules.assistant.domain.entities.exchange import Answer
from src.modules.assistant.domain.entities.unanswered import Unanswered


class Answerer(ABC):
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Whether there is a model to ask at all."""
        ...

    @abstractmethod
    async def answer(
        self, conversation: Conversation, question: str, project_id: int | None
    ) -> Answer | Unanswered: ...
