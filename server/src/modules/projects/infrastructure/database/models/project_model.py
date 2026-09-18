"""SQLAlchemy model of the mission reference list."""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.modules.projects.domain.entities.project import (
    ProjectCategory,
    ProjectKind,
    ProjectPriority,
    ProjectStatus,
)


class ProjectModel(Base):
    """Table of projects, work packages and off-project work."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(String(255))
    kind: Mapped[ProjectKind] = mapped_column(
        Enum(ProjectKind, name="project_kind", native_enum=False, length=16),
        index=True,
    )
    status: Mapped[ProjectStatus | None] = mapped_column(
        Enum(ProjectStatus, name="project_status", native_enum=False, length=16),
        nullable=True,
    )
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    #: When the mission left the reference list. Null while it is active.
    archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    estimated_days: Mapped[float | None] = mapped_column(Float, nullable=True)
    category: Mapped[ProjectCategory | None] = mapped_column(
        Enum(ProjectCategory, name="project_category", native_enum=False, length=32),
        nullable=True,
    )
    priority: Mapped[ProjectPriority | None] = mapped_column(
        Enum(ProjectPriority, name="project_priority", native_enum=False, length=16),
        nullable=True,
    )
    go_live_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_contacts: Mapped[str | None] = mapped_column(Text, nullable=True)
    #: Rank within its board column.
    position: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Rattachement Monday : inutilise en V1, alimente en V1.1.
    monday_item_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    monday_subitem_id: Mapped[str | None] = mapped_column(String(32), nullable=True)

    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
