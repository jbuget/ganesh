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
        UniqueConstraint("user_id", "project_id", "day", name="uq_entry_slot"),
        CheckConstraint("value IN (0.5, 1.0)", name="ck_entry_value"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), index=True
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
        UniqueConstraint("user_id", "project_id", "month", name="uq_user_mission"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    month: Mapped[date] = mapped_column(Date, index=True)
