"""SQLAlchemy model for the activities of a mission."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.shared.enums.work_nature import WorkNature


class ActivityModel(Base):
    """An activity: a trade a mission's days are booked under."""

    __tablename__ = "activities"
    __table_args__ = (
        # One trade, once per mission. A partial index rather than a plain
        # constraint: an archived activity no longer holds the place, which
        # is how a budget is started over without losing the days booked
        # against the old line. NULLS NOT DISTINCT so that « no trade stated »
        # is itself unique — two of those would be as undecidable as two
        # « Développement ».
        Index(
            "uq_activity_trade",
            "project_id",
            "nature",
            unique=True,
            postgresql_where=text("is_active"),
            postgresql_nulls_not_distinct=True,
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    #: Cascade rather than restrict: the activities of a mission are part of
    #: it, and a mission deleted takes its own cut-up with it. The entries
    #: hold the line — they restrict on the mission, so nothing is ever
    #: deleted out from under days already declared.
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    label: Mapped[str] = mapped_column(String(255))
    nature: Mapped[WorkNature | None] = mapped_column(
        Enum(WorkNature, name="work_nature", native_enum=False, length=32),
        nullable=True,
        index=True,
    )
    estimated_days: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    #: When the activity left the mission. Null while it is active.
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
