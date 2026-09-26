"""SQLAlchemy model for the dates a mission answers for."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class MilestoneModel(Base):
    """A milestone: a day a mission is expected at, and the day it got there."""

    __tablename__ = "milestones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    #: Cascade rather than restrict: the milestones of a mission are part of
    #: it, and a mission deleted takes its own dates with it. Nothing is ever
    #: booked against one, so no declared day hangs off the other end.
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    label: Mapped[str] = mapped_column(String(255))
    #: The day announced. Indexed with the mission: the sheet reads one
    #: mission's milestones in the order they happen, every time it opens.
    expected_on: Mapped[date] = mapped_column(Date, index=True)
    #: The day it actually happened. Null until it does.
    reached_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    #: Stamped by the database rather than by the application: a row changed
    #: by a migration or by hand must move it too, or it would say something
    #: false. What a reader actually reads is the journal, in sentences.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
