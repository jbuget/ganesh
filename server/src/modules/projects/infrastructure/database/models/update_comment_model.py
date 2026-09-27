"""SQLAlchemy model of the replies written under an update."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class UpdateCommentModel(Base):
    """Table of the comments posted under an update.

    The foreign key points at an update and never at another comment: the
    depth of one is carried by the schema rather than by a rule, so no gesture
    can make the conversation deeper than it was designed to be.

    Nothing is erased, as above: a withdrawal sets a date and empties the
    text, and the conversation keeps its order.
    """

    __tablename__ = "project_update_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    update_id: Mapped[int] = mapped_column(
        ForeignKey("project_updates.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    body: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    edited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
