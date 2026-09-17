"""Modele SQLAlchemy des jours feries.

La table sert de reference partagee et permet d'ajuster un jour chome
specifique a l'entreprise sans toucher au code.
"""

from datetime import date

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class HolidayModel(Base):
    """Un jour ferie ou chome."""

    __tablename__ = "holidays"

    day: Mapped[date] = mapped_column(Date, primary_key=True)
    label: Mapped[str] = mapped_column(String(128))
