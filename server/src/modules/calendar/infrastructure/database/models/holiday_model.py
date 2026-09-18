"""SQLAlchemy model of public holidays.

The table acts as a shared reference and allows adjusting a company-specific
non-working day without touching the code.
"""

from datetime import date

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class HolidayModel(Base):
    """A public or company holiday."""

    __tablename__ = "holidays"

    day: Mapped[date] = mapped_column(Date, primary_key=True)
    label: Mapped[str] = mapped_column(String(128))
