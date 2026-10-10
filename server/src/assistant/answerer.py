"""Port for the model that answers.

It is handed the conversation so far and the new question, and hands back an
answer or nothing at all. Nothing is a normal outcome — no key configured, the
provider down, a model that kept asking for tools and never wrote — and the
assistant says so to whoever asked.
"""

from abc import ABC, abstractmethod

from src.modules.assistant.domain.entities.conversation import Conversation
from src.modules.assistant.domain.entities.exchange import Answer


class Answerer(ABC):
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Whether there is a model to ask at all."""
        ...

    @abstractmethod
    async def answer(
        self, conversation: Conversation, question: str, project_id: int | None
    ) -> Answer | None: ...
