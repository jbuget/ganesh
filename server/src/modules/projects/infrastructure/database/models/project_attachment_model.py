"""SQLAlchemy model of the files a mission carries."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class ProjectAttachmentModel(Base):
    """Table of the files dropped on a mission.

    The row says what the file is called and where its bytes sit; the bytes
    themselves are in the object store. Deleting a mission takes the rows by
    cascade — the use case takes the objects, which no cascade can reach.
    """

    __tablename__ = "project_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    uploaded_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(255))
    # BigInteger rather than Integer: a size in bytes is not a count of rows,
    # and the column should not be the thing that caps what a file may weigh.
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    storage_key: Mapped[str] = mapped_column(String(512), unique=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
