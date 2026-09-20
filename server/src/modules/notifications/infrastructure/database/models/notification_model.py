"""SQLAlchemy model for what people are told."""

from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Enum, ForeignKey, Index, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.modules.notifications.domain.entities.notification import NotificationKind


class NotificationModel(Base):
    """One line of someone's inbox.

    The actor and the mission are released rather than cascaded: a line
    survives the account or the mission it names being removed, exactly as the
    audit log does. What it takes to still read such a line is carried in the
    payload at the moment it is written.
    """

    __tablename__ = "notifications"
    __table_args__ = (
        # The one query the bell and the panel both make: my lines, the unread
        # ones first to hand, most recent first.
        Index(
            "ix_notification_inbox",
            "recipient_id",
            "read_at",
            "at",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[NotificationKind] = mapped_column(
        Enum(NotificationKind, name="notification_kind", native_enum=False, length=32),
        index=True,
    )
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    #: The month, for everything that concerns a timesheet; a day for nothing
    #: else. It is what folds two edits on one month into a single line.
    day: Mapped[date | None] = mapped_column(Date, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    #: How many times the same gesture folded into this line. One, usually.
    count: Mapped[int] = mapped_column(Integer, server_default="1")
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
