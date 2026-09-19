"""SQLAlchemy model for the moods the team posts."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.modules.moods.domain.entities.mood import MoodLevel


class MoodModel(Base):
    """How a day felt, for one teammate.

    One row per person and per day: posting again changes the row rather than
    adding to it, and the constraint is what guarantees it.
    """

    __tablename__ = "moods"
    __table_args__ = (UniqueConstraint("user_id", "day", name="uq_mood_slot"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    day: Mapped[date] = mapped_column(Date, index=True)
    level: Mapped[MoodLevel] = mapped_column(
        Enum(MoodLevel, name="mood_level", native_enum=False, length=16)
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
