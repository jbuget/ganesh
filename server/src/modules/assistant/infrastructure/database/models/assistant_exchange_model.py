"""SQLAlchemy model of an exchange with the assistant."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.modules.assistant.domain.entities.exchange import Verdict


class AssistantExchangeModel(Base):
    """One question and its answer, kept to study the assistant.

    A conversation has no table of its own: it is the exchanges that carry its
    identifier, and it exists from its first one. The person goes with their
    account; the project is released, the question still saying what was asked.
    """

    __tablename__ = "assistant_exchanges"
    __table_args__ = (
        UniqueConstraint("conversation_id", "rank", name="uq_assistant_exchange_rank"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    #: Read through the unique constraint, which leads with it: no index of
    #: its own.
    conversation_id: Mapped[UUID] = mapped_column(Uuid)
    rank: Mapped[int] = mapped_column(SmallInteger)
    asker_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    #: What each tool was asked and read back, in the order the model asked.
    consultations: Mapped[list] = mapped_column(JSON)
    model: Mapped[str] = mapped_column(String(120))
    input_tokens: Mapped[int] = mapped_column(Integer)
    output_tokens: Mapped[int] = mapped_column(Integer)
    elapsed_ms: Mapped[int] = mapped_column(Integer)
    verdict: Mapped[Verdict | None] = mapped_column(
        Enum(Verdict, name="assistant_verdict", native_enum=False, length=16),
        nullable=True,
    )
    asked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
