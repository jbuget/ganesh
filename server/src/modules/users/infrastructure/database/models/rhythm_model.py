"""SQLAlchemy model of the rhythms teammates declare."""

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base

#: Each day of the motif holds what an entry holds, or nothing at all.
_VALUES = "IN (0, 0.5, 1)"


class WorkRhythmModel(Base):
    """A week motif, from the day it took effect.

    A row is never updated but for a correction opening the same day: a new
    rhythm is a new row, and the ones before it are what makes a past month
    readable with what that month knew.
    """

    __tablename__ = "work_rhythms"
    __table_args__ = (
        UniqueConstraint("user_id", "effective_from", name="uq_rhythm_opening"),
        CheckConstraint(
            " AND ".join(
                f"{day} {_VALUES}"
                for day in ("monday", "tuesday", "wednesday", "thursday", "friday")
            ),
            name="ck_rhythm_values",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    #: The day the motif opens on. A rhythm holds until the next one opens.
    effective_from: Mapped[date] = mapped_column(Date, index=True)

    monday: Mapped[float] = mapped_column(Float)
    tuesday: Mapped[float] = mapped_column(Float)
    wednesday: Mapped[float] = mapped_column(Float)
    thursday: Mapped[float] = mapped_column(Float)
    friday: Mapped[float] = mapped_column(Float)

    declared_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
