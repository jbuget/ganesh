"""SQLAlchemy model of a generated digest."""

from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class GazetteDigestModel(Base):
    """One generation of one month, kept as it read that day.

    The facts are kept rather than the way to recompute them: missions get
    renamed, archived and delivered, and rebuilding March in September would
    give another March. Nothing is ever updated here — asking for a month
    again writes the next version beside this one.
    """

    __tablename__ = "gazette_digests"
    __table_args__ = (
        UniqueConstraint("month", "version", name="uq_gazette_digest_version"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    #: The first day of the month covered.
    month: Mapped[date] = mapped_column(Date, index=True)
    version: Mapped[int] = mapped_column(Integer)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    #: Who asked for it, as it was written that day. A name rather than a
    #: foreign key: a digest is an archive, and it must not change wording
    #: because somebody's display name did, nor lose its byline if they leave.
    requested_by: Mapped[str] = mapped_column(String(255))
    brief: Mapped[dict] = mapped_column(JSON)
    prose: Mapped[str | None] = mapped_column(Text, nullable=True)
    prose_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
