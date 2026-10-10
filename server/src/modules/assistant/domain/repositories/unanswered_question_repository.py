"""Port for the questions the assistant could not answer."""

from abc import ABC, abstractmethod

from src.modules.assistant.domain.entities.unanswered import UnansweredQuestion


class UnansweredQuestionRepository(ABC):
    @abstractmethod
    async def add(self, question: UnansweredQuestion) -> UnansweredQuestion:
        """Keeps the question and hands it back with its identifier."""
        ...
