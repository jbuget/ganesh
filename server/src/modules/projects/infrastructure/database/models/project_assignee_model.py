"""SQLAlchemy model for the contributors assigned to a mission."""

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.modules.projects.domain.entities.project_role import ProjectRole


class ProjectAssigneeModel(Base):
    """Join table between a mission and its contributors.

    The primary key carries all three columns: the same person cannot hold the
    same role twice on a mission, and adding becomes idempotent without any
    code checking for it. They may however be both lead and contributor, which
    happens often.
    """

    __tablename__ = "project_assignees"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[ProjectRole] = mapped_column(
        Enum(ProjectRole, name="project_role", native_enum=False, length=16),
        primary_key=True,
        server_default=ProjectRole.CONTRIBUTOR.name,
    )
