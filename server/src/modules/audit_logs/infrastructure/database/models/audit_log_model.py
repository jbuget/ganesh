"""SQLAlchemy model of the audit log."""

from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Enum, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.modules.audit_logs.domain.entities.audit_log import AuditAction


class AuditLogModel(Base):
    """Immutable trace of the actions that matter."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, name="audit_action", native_enum=False, length=32),
        index=True,
    )
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    target_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    request_id: Mapped[int | None] = mapped_column(
        ForeignKey("requests.id", ondelete="SET NULL"), nullable=True, index=True
    )
    day: Mapped[date | None] = mapped_column(Date, nullable=True)
    #: What a field moved from and to, as it was typed. Held without a width:
    #: a documentation address, a summary or a list of scopes all run past any
    #: line one would have guessed, and a column that refused them turned an
    #: ordinary edit into a 500.
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
