"""SQLAlchemy models for entries and the missions of a month."""

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.modules.projects.domain.entities.project import ProjectStatus


class EntryModel(Base):
    """An entry: a user, a mission, a day."""

    __tablename__ = "entries"
    __table_args__ = (
        # NULLS NOT DISTINCT, because the activity is null on off-project work
        # and on everything the reprise took over: left distinct, Postgres
        # would let the same person book the same day twice on the same
        # mission, which is exactly what this constraint exists to prevent.
        UniqueConstraint(
            "user_id",
            "project_id",
            "activity_id",
            "day",
            name="uq_entry_slot",
            postgresql_nulls_not_distinct=True,
        ),
        CheckConstraint("value IN (0.5, 1.0)", name="ck_entry_value"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), index=True
    )
    #: The activity the day is booked under. Null on off-project work, which
    #: is booked against directly, and on what the reprise took over, where
    #: nobody ever declared a trade. Restrict rather than cascade: an activity
    #: carrying declared days is not deleted out from under them.
    activity_id: Mapped[int | None] = mapped_column(
        ForeignKey("activities.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    day: Mapped[date] = mapped_column(Date, index=True)
    value: Mapped[float] = mapped_column(Float)

    # Snapshot of the project status at entry time: makes it possible to
    # measure time consumed per phase.
    status_at_entry: Mapped[ProjectStatus | None] = mapped_column(
        Enum(ProjectStatus, name="project_status", native_enum=False, length=16),
        nullable=True,
    )

    updated_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class UserMissionModel(Base):
    """The missions a user added to their month."""

    __tablename__ = "user_missions"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "project_id",
            "activity_id",
            "month",
            name="uq_user_mission",
            postgresql_nulls_not_distinct=True,
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    #: The activity the line stands for. Null for off-project work, which is
    #: added to a month as itself.
    activity_id: Mapped[int | None] = mapped_column(
        ForeignKey("activities.id", ondelete="CASCADE"), nullable=True, index=True
    )
    month: Mapped[date] = mapped_column(Date, index=True)
