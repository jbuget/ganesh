"""SQLAlchemy model of a share link."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class GazetteShareLinkModel(Base):
    """A way in to one version of one digest, open until somebody closes it.

    The token is kept as drawn rather than hashed, unlike an API key's secret:
    a key gives a power, where this gives the reading of a digest that sits in
    the same database — a leak that exposed the tokens would already have
    exposed what they open. Keeping it is what lets the team copy a link that
    was made last week.
    """

    __tablename__ = "gazette_share_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    digest_id: Mapped[int] = mapped_column(ForeignKey("gazette_digests.id"), index=True)
    token: Mapped[str] = mapped_column(String(128), unique=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
