"""SQLAlchemy implementation of the UnansweredQuestionRepository port."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.assistant.domain.entities.unanswered import (
    Unanswered,
    UnansweredQuestion,
)
from src.modules.assistant.domain.repositories.unanswered_question_repository import (
    UnansweredQuestionRepository,
)
from src.modules.assistant.infrastructure.database.models.assistant_unanswered_question_model import (
    AssistantUnansweredQuestionModel,
)
from src.modules.assistant.infrastructure.database.repositories.exchange_repository_impl import (
    consultation_of,
    held_as,
)


def to_unanswered_entity(model: AssistantUnansweredQuestionModel) -> UnansweredQuestion:
    return UnansweredQuestion(
        id=model.id,
        conversation_id=model.conversation_id,
        asker_id=model.asker_id,
        question=model.question,
        unanswered=Unanswered(
            reason=model.reason,
            consultations=tuple(consultation_of(held) for held in model.consultations),
            model=model.model,
            input_tokens=model.input_tokens,
            output_tokens=model.output_tokens,
            elapsed_ms=model.elapsed_ms,
        ),
        project_id=model.project_id,
        asked_at=model.asked_at,
    )


class SqlUnansweredQuestionRepository(UnansweredQuestionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, question: UnansweredQuestion) -> UnansweredQuestion:
        unanswered = question.unanswered
        model = AssistantUnansweredQuestionModel(
            conversation_id=question.conversation_id,
            asker_id=question.asker_id,
            project_id=question.project_id,
            question=question.question,
            reason=unanswered.reason,
            consultations=[held_as(held) for held in unanswered.consultations],
            model=unanswered.model,
            input_tokens=unanswered.input_tokens,
            output_tokens=unanswered.output_tokens,
            elapsed_ms=unanswered.elapsed_ms,
            asked_at=question.asked_at,
        )
        self._session.add(model)
        await self._session.flush()
        return to_unanswered_entity(model)
