"""Keeping a question the assistant could not answer."""

from src.modules.assistant.application.dtos.assistant_dtos import (
    RecordUnansweredCommand,
)
from src.modules.assistant.domain.entities.unanswered import UnansweredQuestion
from src.modules.assistant.domain.repositories.unanswered_question_repository import (
    UnansweredQuestionRepository,
)
from src.shared.utils import clock


class RecordUnansweredUseCase:
    """Keeps the question, why it went unanswered, and what was read meanwhile.

    The questions that fail are the ones most worth studying: they are what a
    reader met as « indisponible », and the log alone does not say what was
    asked.
    """

    def __init__(self, questions: UnansweredQuestionRepository) -> None:
        self._questions = questions

    async def execute(self, command: RecordUnansweredCommand) -> UnansweredQuestion:
        admitted = command.admitted
        return await self._questions.add(
            admitted.conversation.missed(
                admitted.question,
                command.unanswered,
                project_id=admitted.project_id,
                asked_at=clock.now(),
            )
        )
