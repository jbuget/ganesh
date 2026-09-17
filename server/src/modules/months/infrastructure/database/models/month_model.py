"""Modele SQLAlchemy de l'etat de saisie des mois."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.modules.months.domain.entities.month import MonthState


class MonthModel(Base):
    """Etat de saisie d'un mois, pour un utilisateur."""

    __tablename__ = "month_status"
    __table_args__ = (UniqueConstraint("user_id", "month", name="uq_month_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    month: Mapped[date] = mapped_column(Date, index=True)
    state: Mapped[MonthState] = mapped_column(
        Enum(MonthState, name="month_state", native_enum=False, length=16),
        default=MonthState.OPEN,
    )
    validated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    validated_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reopened_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reopened_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
