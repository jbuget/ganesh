"""SQLAlchemy model of a question the assistant could not answer."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.modules.assistant.domain.entities.unanswered import WhyUnanswered


class AssistantUnansweredQuestionModel(Base):
    """A question, why no answer came, and what was read meanwhile.

    Beside `assistant_exchanges` rather than in it: no answer, no verdict, no
    annotation, no rank in its conversation.
    """

    __tablename__ = "assistant_unanswered_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[UUID] = mapped_column(Uuid)
    asker_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    question: Mapped[str] = mapped_column(Text)
    reason: Mapped[WhyUnanswered] = mapped_column(
        Enum(
            WhyUnanswered,
            name="assistant_unanswered_reason",
            native_enum=False,
            length=32,
        )
    )
    #: What each tool was asked and read back before no answer came.
    consultations: Mapped[list] = mapped_column(JSON)
    model: Mapped[str] = mapped_column(String(120))
    input_tokens: Mapped[int] = mapped_column(Integer)
    output_tokens: Mapped[int] = mapped_column(Integer)
    elapsed_ms: Mapped[int] = mapped_column(Integer)
    asked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
