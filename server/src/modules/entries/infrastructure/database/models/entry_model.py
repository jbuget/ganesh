"""Modeles SQLAlchemy des saisies et des missions du mois."""

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
    """Une saisie : un utilisateur, une mission, un jour."""

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

    # Photo du statut du projet au moment de la saisie : permet de mesurer le
    # temps consomme par phase.
    status_at_entry: Mapped[ProjectStatus | None] = mapped_column(
        Enum(ProjectStatus, name="project_status", native_enum=False, length=16),
        nullable=True,
    )

    updated_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class UserMissionModel(Base):
    """Les missions qu'un utilisateur a ajoutees a son mois."""

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
