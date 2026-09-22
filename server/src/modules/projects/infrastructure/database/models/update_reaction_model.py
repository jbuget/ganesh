"""SQLAlchemy model of the signs left under an update."""

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.modules.projects.domain.entities.update_reaction import Reaction


class UpdateReactionModel(Base):
    """Table of the reactions posted on an update.

    The primary key carries all three columns: the same person cannot leave
    the same sign twice on the same update, and leaving it again becomes
    idempotent without any code checking for it. They may leave several
    different ones, which is the point.
    """

    __tablename__ = "project_update_reactions"

    update_id: Mapped[int] = mapped_column(
        ForeignKey("project_updates.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    reaction: Mapped[Reaction] = mapped_column(
        Enum(Reaction, name="update_reaction", native_enum=False, length=16),
        primary_key=True,
    )
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
