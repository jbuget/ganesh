"""SQLAlchemy model of the signs left under a comment."""

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.modules.projects.domain.entities.update_reaction import Reaction


class CommentReactionModel(Base):
    """Table of the reactions posted on a comment.

    The primary key carries all three columns, as an update's does: the same
    person cannot leave the same sign twice on the same reply, and leaving it
    again is idempotent without any code checking for it.

    The enumeration is the one declared beside the update's, and the database
    type is shared: two closed sets that could drift apart would be two
    answers to « what may one leave under a message ».
    """

    __tablename__ = "project_update_comment_reactions"

    comment_id: Mapped[int] = mapped_column(
        ForeignKey("project_update_comments.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    reaction: Mapped[Reaction] = mapped_column(
        Enum(Reaction, name="update_reaction", native_enum=False, length=16),
        primary_key=True,
    )
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
